import mknodes as mk


nav = mk.MkNav("Internals")


@nav.route.nav("Complete code")
def _(nav: mk.MkNav):
    nav.parse.module("mkdocs_mknodes/manual/", hide="toc")
