from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from mkdocs_mknodes import cli
from mkdocs_mknodes.generator import (
    BuildOutput,
    GeneratorSettings,
    NavItem,
    generate_output,
    generator as generator_mod,
    yamlconfig,
)
from mkdocs_mknodes.writers import GeneratedFolder, ZensicalWriter
from mkdocs_mknodes.writers.zensical import (
    merge_markdown_extensions,
    nav_to_config,
    social_to_config,
)


REPO_ROOT = pathlib.Path(__file__).parent.parent

BUILD_SCRIPT = """\
import mknodes as mk


def build(root, theme, greeting="Hello"):
    page = root.add_page("Intro", is_index=True)
    page += mk.MkAdmonition(greeting, typ="info")
    section = root.add_nav("Section")
    details = section.add_page("Details")
    details += mk.MkText("Back to the [intro](index.md).")
    other = section.add_page("Other")
    other += mk.MkText("Other page")
"""

MKDOCS_YML = """\
site_name: Fixture
theme:
  name: material
  custom_dir: overrides
plugins:
  - search
  - mknodes:
      build_fn: build.py:build
      repo_path: {repo}
      show_page_info: !ENV [MKNODES_TEST_UNSET_VAR, false]
      kwargs:
        greeting: Hi there
markdown_extensions:
  - toc:
      permalink: true
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
nav:
  - Handwritten: handwritten.md
"""


@pytest.fixture
def project(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "build.py").write_text(BUILD_SCRIPT)
    (tmp_path / "mkdocs.yml").write_text(MKDOCS_YML.format(repo=REPO_ROOT.as_posix()))
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "handwritten.md").write_text("# Hand-written\n")
    (tmp_path / "overrides").mkdir()
    return tmp_path


def _settings(project: pathlib.Path, **kwargs) -> GeneratorSettings:
    return GeneratorSettings.load(project, **kwargs)


def test_yaml_roundtrip_keeps_tags():
    text = "a: !ENV [X, 1]\nb: !!python/name:os.path.join\nc: [1, 2]\n"
    data = yamlconfig.loads(text)
    assert isinstance(data["a"], yamlconfig.Tagged)
    dumped = yamlconfig.dumps({**data, "d": GeneratorSettings.load, "e": yamlconfig.loads})
    assert "!ENV" in dumped
    assert "!!python/name:os.path.join" in dumped
    assert "!!python/name:mkdocs_mknodes.generator.settings.GeneratorSettings.load" in dumped
    assert "!!python/name:mkdocs_mknodes.generator.yamlconfig.loads" in dumped


def test_settings_from_mkdocs_yml(project: pathlib.Path):
    settings = _settings(project)
    assert settings.build_fn == "build.py:build"
    assert settings.kwargs == {"greeting": "Hi there"}
    assert settings.show_page_info is False  # !ENV fallback
    assert settings.resolved_docs_dir == project / "docs"


def test_settings_pyproject_and_overrides_win(project: pathlib.Path):
    (project / "pyproject.toml").write_text(
        '[tool.mknodes]\nallowed-commit-types = ["fix"]\nbuild-fn = "other:fn"\n'
        'generated-dir = "gen"\n'
    )
    settings = _settings(project)
    assert settings.build_fn == "other:fn"
    assert settings.generated_dir == "gen"
    settings = _settings(project, build_fn="third:fn", clone_depth=None)
    assert settings.build_fn == "third:fn"
    assert settings.clone_depth == 100  # noqa: PLR2004


def test_zero_config_uses_default_website(tmp_path: pathlib.Path):
    settings = GeneratorSettings.load(tmp_path)
    assert settings.build_fn == "mkdocs_mknodes:parse"
    assert settings.config_file is None
    assert settings.kwargs == {}


def test_merge_markdown_extensions():
    configured = [
        "attr_list",
        {"toc": {"permalink": True}},
        {"pymdownx.superfences": {"custom_fences": [{"name": "mermaid", "class": "mermaid"}]}},
    ]
    required = {
        "toc": {"title": "Contents"},
        "admonition": {},
        "pymdownx.superfences": {"custom_fences": [{"name": "mermaid", "class": "mermaid"}]},
    }
    merged = merge_markdown_extensions(configured, required)
    assert merged[0] == "attr_list"
    assert {"toc": {"permalink": True, "title": "Contents"}} in merged
    assert "admonition" in merged
    fences = next(i for i in merged if isinstance(i, dict) and "pymdownx.superfences" in i)
    assert len(fences["pymdownx.superfences"]["custom_fences"]) == 1


def test_nav_and_social_conversion():
    nav = [NavItem("Home", "index.md"), NavItem("API", children=[NavItem("A", "API/a.md")])]
    assert nav_to_config(nav) == [{"Home": "index.md"}, {"API": [{"A": "API/a.md"}]}]
    social = [{"icon": "fa-brands:github", "link": "x"}, {"icon": "unknown:x", "link": "y"}]
    assert social_to_config(social) == [{"icon": "fontawesome/brands/github", "link": "x"}]


def test_resolve_url_collisions():
    output = BuildOutput(
        pages={"API/foo.md": "class", "API/foo/index.md": "module"},
        nav=[
            NavItem("Foo", "API/foo.md"),
            NavItem("foo", children=[NavItem("foo", "API/foo/index.md")]),
        ],
    )
    generator_mod.resolve_url_collisions(output)
    assert set(output.pages) == {"API/foo-1.md", "API/foo/index.md"}
    assert output.nav[0].target == "API/foo-1.md"


def test_generated_folder_never_clobbers(tmp_path: pathlib.Path):
    (tmp_path / "manual.md").write_text("mine")
    folder = GeneratedFolder(tmp_path)
    assert not folder.write("manual.md", "generated")
    assert folder.write("gen/page.md", "generated")
    folder.finish()
    assert (tmp_path / "manual.md").read_text() == "mine"
    manifest = (tmp_path / ".gitignore").read_text().splitlines()
    assert "/gen/page.md" in manifest
    assert "/manual.md" not in manifest
    # second run: the generated page is gone -> stale file gets removed
    folder = GeneratedFolder(tmp_path)
    assert folder.write("gen/other.md", "generated")
    assert folder.finish() == ["gen/page.md"]
    assert not (tmp_path / "gen" / "page.md").exists()
    assert (tmp_path / "manual.md").exists()


def test_generated_folder_respects_existing_gitignore(tmp_path: pathlib.Path):
    (tmp_path / ".gitignore").write_text("*.tmp\n")
    folder = GeneratedFolder(tmp_path)
    folder.write("page.md", "x")
    folder.finish()
    assert (tmp_path / ".gitignore").read_text() == "*.tmp\n"
    assert "/page.md" in (tmp_path / ".mknodes-generated").read_text()


def test_generate_and_write(project: pathlib.Path):
    settings = _settings(project)
    output = generate_output(settings)
    assert set(output.pages) >= {"index.md", "Section/details.md", "Section/other.md"}
    assert "Hi there" in output.pages["index.md"]
    assert "admonition" in output.markdown_extensions
    assert [i.title for i in output.nav] == ["Intro", "Section"]
    # bare file links get resolved to the actual page path
    assert "](../index.md)" in output.pages["Section/details.md"]

    (project / "docs" / "index.md").write_text("# Hand-written index\n")
    cfg_path = ZensicalWriter(settings).write(output)

    docs = project / "docs"
    assert (docs / "index.md").read_text() == "# Hand-written index\n"  # not clobbered
    assert (docs / "Section" / "details.md").is_file()
    assert (docs / "handwritten.md").read_text() == "# Hand-written\n"
    manifest = (docs / ".gitignore").read_text()
    assert "/Section/details.md" in manifest
    assert "/index.md" not in manifest
    assert "/handwritten.md" not in manifest

    text = cfg_path.read_text()
    assert text.startswith("# Generated by mkdocs-mknodes")
    assert "!!python/name:material.extensions.emoji.twemoji" in text
    cfg = yamlconfig.loads(text)
    assert cfg["INHERIT"] == "mkdocs.yml"
    assert cfg["nav"][0] == {"Handwritten": "handwritten.md"}
    assert {"Section": [{"Details": "Section/details.md"}, {"Other": "Section/other.md"}]} in (
        cfg["nav"]
    )
    exts = {next(iter(e)) if isinstance(e, dict) else e: e for e in cfg["markdown_extensions"]}
    assert exts["toc"] == {"toc": {"permalink": True}}
    assert "admonition" in exts
    for css in cfg["extra_css"]:
        assert (docs / css).is_file()
    assert "site_name" not in cfg  # user value is kept

    # regenerating without changes keeps files untouched
    writer = ZensicalWriter(settings)
    writer.write(output)
    assert writer.folder.changed == []


@pytest.mark.skipif(not importlib.util.find_spec("zensical"), reason="zensical not installed")
def test_zensical_builds_generated_site(project: pathlib.Path):
    settings = _settings(project)
    cfg_path = ZensicalWriter(settings).write(generate_output(settings))
    cmd = [sys.executable, "-m", "zensical", "build", "-f", str(cfg_path)]
    result = subprocess.run(cmd, cwd=project, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    site = project / "site"
    assert (site / "Section" / "details" / "index.html").is_file()
    assert (site / "handwritten" / "index.html").is_file()
    html = (site / "index.html").read_text()
    assert "admonition" in html


def test_cli_generate(project: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(project)
    result = CliRunner().invoke(cli.cli, ["generate"], catch_exceptions=False)
    assert result.exit_code == 0
    assert (project / "mkdocs.generated.yml").is_file()
    assert (project / "docs" / "Section" / "details.md").is_file()


def test_cli_generate_into_separate_dir(project: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(project)
    args = ["generate", "--generated-dir", "build/docs"]
    result = CliRunner().invoke(cli.cli, args, catch_exceptions=False)
    assert result.exit_code == 0
    gen = project / "build" / "docs"
    assert (gen / "handwritten.md").is_file()  # mirrored
    assert (gen / "Section" / "details.md").is_file()
    assert not (project / "docs" / "Section").exists()
    cfg = yamlconfig.loads((project / "mkdocs.generated.yml").read_text())
    assert cfg["docs_dir"] == "build/docs"


def test_watch_ignores_generated_files(project: pathlib.Path):
    from mkdocs_mknodes.generator import watch

    settings = _settings(project)
    ZensicalWriter(settings).write(generate_output(settings))
    watched = {p.relative_to(project).as_posix() for p in watch.iter_watched_files(settings)}
    assert "build.py" in watched
    assert "docs/handwritten.md" in watched
    assert "mkdocs.yml" in watched
    assert "docs/Section/details.md" not in watched
    assert "mkdocs.generated.yml" not in watched


def test_writer_build_command(project: pathlib.Path):
    writer = ZensicalWriter(_settings(project))
    cmd = writer.build_command(serve=True, extra_args=["--strict"])
    assert cmd[1:4] == ["-m", "zensical", "serve"]
    assert cmd[-1] == "--strict"
    assert cmd[-2].endswith("mkdocs.generated.yml")


def test_icon_resolver_maps_and_downloads_icons():
    from mkdocs_mknodes.writers.zensical import IconResolver

    resolver = IconResolver(fetch=lambda key: f"<svg>{key}</svg>")
    page = "---\nicon: grommet-icons:install\ntitle: X\n---\n\nicon: not front matter\n"
    result = resolver.update_page(page)
    assert "icon: iconify/grommet-icons/install\n" in result
    assert result.endswith("\nicon: not front matter\n")
    assert resolver.svgs == {
        ".icons/iconify/grommet-icons/install.svg": "<svg>grommet-icons:install</svg>"
    }
    assert resolver.resolve("mdi:wrench") == "material/wrench"
    social = resolver.update_social([{"icon": "fa-brands:github", "link": "x"}])
    assert social == [{"icon": "fontawesome/brands/github", "link": "x"}]
    failing = IconResolver(fetch=lambda _key: None)
    assert "icon:" not in failing.update_page("---\nicon: foo:bar\n---\n")
