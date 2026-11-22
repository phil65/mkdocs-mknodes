from __future__ import annotations

from unittest import mock

import pytest
from typer.testing import CliRunner

from mkdocs_mknodes import cli


@pytest.fixture
def generate():
    writer = mock.Mock()
    writer.build_command.return_value = ["zensical", "build"]
    with mock.patch("mkdocs_mknodes.cli._generate", return_value=writer) as mocked:
        yield mocked


@pytest.mark.parametrize("engine_args", [[], ["--engine", "zensical"], ["-e", "zensical"]])
def test_build(generate, engine_args: list[str]):
    build_fn = "mkdocs_mknodes:MkDefaultWebsite"
    args = ["build", "--config-path", "mkdocs.yml", "--build-fn", build_fn, "-s"]
    with mock.patch("subprocess.call", return_value=0) as call:
        result = CliRunner().invoke(cli.cli, args + engine_args, catch_exceptions=False)
    assert result.exit_code == 0
    settings, engine = generate.call_args.args
    assert engine == "zensical"
    assert settings.build_fn == build_fn
    writer = generate.return_value
    writer.build_command.assert_called_once_with(extra_args=["--strict"])
    call.assert_called_once_with(["zensical", "build"])


def test_build_propagates_exit_code(generate):
    with mock.patch("subprocess.call", return_value=3):
        result = CliRunner().invoke(cli.cli, ["build"], catch_exceptions=False)
    assert result.exit_code == 3  # noqa: PLR2004


@pytest.mark.parametrize("command", ["build", "serve", "generate"])
def test_unsupported_engine_is_rejected(generate, command: str):
    result = CliRunner().invoke(cli.cli, [command, "--engine", "mkdocs"])
    assert result.exit_code == 2  # noqa: PLR2004
    assert "Unsupported engine 'mkdocs'" in result.output
    generate.assert_not_called()


def test_removed_commands():
    result = CliRunner().invoke(cli.cli, ["create-config"])
    assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])
