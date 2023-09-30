from __future__ import annotations

import dataclasses

from mknodes.utils import helpers, log


logger = log.get_logger(__name__)

# // Primary color shades
# --md-primary-fg-color:               hsla(#{hex2hsl($clr-indigo-500)}, 1);
# --md-primary-fg-color--light:        hsla(#{hex2hsl($clr-indigo-400)}, 1);
# --md-primary-fg-color--dark:         hsla(#{hex2hsl($clr-indigo-700)}, 1);
# --md-primary-bg-color:               hsla(0, 0%, 100%, 1);
# --md-primary-bg-color--light:        hsla(0, 0%, 100%, 0.7);

# // Accent color shades
# --md-accent-fg-color:                hsla(#{hex2hsl($clr-indigo-a200)}, 1);
# --md-accent-fg-color--transparent:   hsla(#{hex2hsl($clr-indigo-a200)}, 0.1);
# --md-accent-bg-color:                hsla(0, 0%, 100%, 1);
# --md-accent-bg-color--light:         hsla(0, 0%, 100%, 0.7);


@dataclasses.dataclass
class ColorTheme:
    color: str
    light_shade: str | None = None
    dark_shade: str | None = None

    @property
    def color_str(self) -> str:
        return helpers.get_color_str(self.color)

    @property
    def light_str(self) -> str:
        return helpers.get_color_str(self.light_shade or self.color)

    @property
    def dark_str(self) -> str:
        return helpers.get_color_str(self.dark_shade or self.color)


if __name__ == "__main__":
    color_theme = ColorTheme("#FFFFFF")
    print(color_theme)
