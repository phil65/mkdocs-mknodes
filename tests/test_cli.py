from __future__ import annotations

import pathlib
import tempfile

from unittest import mock

from typer.testing import CliRunner

from mkdocs_mknodes import cli


_dir = tempfile.TemporaryDirectory(prefix="mknodes_")
build_folder = pathlib.Path(_dir.name)


@mock.patch("mkdocs_mknodes.commands.build_page.build", autospec=True)
def test_build(mock_build):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["build", "--config-path", "mkdocs.yml"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    mock_build.assert_called_once_with(
        config_path="mkdocs.yml",
        repo_path=None,
        build_fn=None,
        clone_depth=None,
        site_dir="site",
        strict=False,
        theme=None,
        use_directory_urls=True,
    )


@mock.patch("mkdocs.livereload.LiveReloadServer.serve", autospec=True)
@mock.patch("mkdocs_mknodes.commands.build_page._build", autospec=True)
def test_serve_default(mock_build, mock_serve):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["serve", "--config-path", "configs/mkdocs_mkdocs.yml"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    mock_build.assert_called_once()


def test_create_config():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["create-config"], catch_exceptions=False)
    assert result.exit_code == 0
