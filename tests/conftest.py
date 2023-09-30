from __future__ import annotations

from mknodes import project as project_
from mknodes.theme import materialtheme
import pytest

from mkdocs_mknodes import mkdocsconfig


@pytest.fixture(scope="session")
def config():
    return mkdocsconfig.Config()


@pytest.fixture(scope="session")
def project():
    skin = materialtheme.MaterialTheme()
    return project_.Project(skin)
