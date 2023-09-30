from __future__ import annotations

import pathlib

import pytest

# from responsemock import utils
from mknodes import manual, project as project_


RESPONSE_1 = """{
  "name": "mkdocstrings",
  "url": "https://api.github.com/repos/mkdocstrings/mkdocstrings",
  "size": 3249,
  "default_branch": "main"
}"""

RESPONSE_2 = """{
  "sha": "0a90a474c8dcbd95821700d7dab63f03e392c40f",
  "url": "https://api.github.com/repos/mkdocstrings/mkdocstrings/git/trees/0a90a474c8dcbd95821700d7dab63f03e392c40f",
  "tree": [
    {
      "path": "scripts",
      "mode": "040000",
      "type": "tree",
      "sha": "b30cc0fde9b9684fc1cdbe8238161c4d85202bcb",
      "url": "https://api.github.com/repos/mkdocstrings/mkdocstrings/git/trees/b30cc0fde9b9684fc1cdbe8238161c4d85202bcb"
    }
  ],
  "truncated": false
}"""

RESPONSE_3 = """{
  "sha": "b30cc0fde9b9684fc1cdbe8238161c4d85202bcb",
  "url": "https://api.github.com/repos/mkdocstrings/mkdocstrings/git/trees/b30cc0fde9b9684fc1cdbe8238161c4d85202bcb",
  "tree": [
    {
      "path": "gen_credits.py",
      "mode": "100644",
      "type": "blob",
      "sha": "bc01c0bd7d85b2820b0d16d1212930b7f5fc2ff0",
      "size": 4734,
      "url": "https://api.github.com/repos/mkdocstrings/mkdocstrings/git/blobs/bc01c0bd7d85b2820b0d16d1212930b7f5fc2ff0"
    }]}"""


@pytest.fixture(scope="session")
def test_data_dir():
    return pathlib.Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def resources_dir():
    return pathlib.Path(__file__).parent.parent / "mknodes/resources/"


@pytest.fixture(scope="session")
def project():
    proj = project_.Project.for_mknodes()
    # with utils.response_mock(
    #     [
    #         (
    #             "GET https://raw.githubusercontent.com/phil65/mknodes/main/README.md ->"
    #             ' 200 :{"default_branch":"main"}'
    #         ),
    #         (
    #             "GET https://api.github.com/repos/mkdocstrings/mkdocstrings -> 200 :"
    #             f" {RESPONSE_1}"
    #         ),
    #         (
    #             "GET https://api.github.com/repos/mkdocstrings/mkdocstrings/git/trees/main"
    #             f" -> 200 :{RESPONSE_2}"
    #         ),
    #         (
    #             "GET https://api.github.com/repos/mkdocstrings/mkdocstrings/git/trees/b30cc0fde9b9684fc1cdbe8238161c4d85202bcb"
    #             f" -> 200 :{RESPONSE_3}"
    #         ),
    #     ],
    # ):
    manual.build(proj)
    return proj
