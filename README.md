# mkdocs-mknodes (merged into mknodes)

This package has been merged into [mknodes](https://github.com/phil65/mknodes) (4.0+), which now
contains the site generator: `mknodes build` / `serve` / `generate`.

```bash
uv add --group docs "mknodes>=4.0.0"
uv run mknodes build
```

Settings stay in `[tool.mknodes]` of `pyproject.toml`. The default build function is now
`mknodes.site:parse` (was `mkdocs_mknodes:parse`); custom build functions are unchanged.

Documentation: https://phil65.github.io/mknodes/

The history of this repository is part of the mknodes repository.
