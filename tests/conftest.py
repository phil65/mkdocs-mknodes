from __future__ import annotations

import pytest

# from responsemock import utils
from mkdocs_mknodes import mkdocsconfig


@pytest.fixture(scope="session")
def config():
    return mkdocsconfig.Config()
