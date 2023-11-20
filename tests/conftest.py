from __future__ import annotations

import pytest

from mkdocs_mknodes import mkdocsconfig


@pytest.fixture(scope="session")
def config():
    return mkdocsconfig.Config()
