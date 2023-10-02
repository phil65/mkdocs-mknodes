import mknodes as mk

from mknodes.theme import materialtheme

from mkdocs_mknodes import manual


def build(project: mk.Project[materialtheme.MaterialTheme]) -> mk.MkNav:
    project.env.add_template_path("mkdocs_mknodes/resources")

    root_nav = project.get_root()
    project.theme.announcement_bar = mk.MkMetadataBadges("websites")
    project.theme.error_page.content = mk.MkAdmonition("Page does not exist!")
    project.theme.content_area_width = 1300
    project.theme.tooltip_width = 800

    manual.create_get_started_section(root_nav)
    manual.create_use_cases_section(root_nav)
    doc = root_nav.add_doc(section_name="API")
    doc.collect_classes(recursive=True)
    manual.create_cli_section(root_nav)
    manual.create_development_section(root_nav)
    return root_nav
