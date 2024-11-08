from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ValidationLevel(Enum):
    warn = "warn"
    info = "info"
    ignore = "ignore"


class ValidationLevelForAbsolute(Enum):
    warn = "warn"
    info = "info"
    ignore = "ignore"
    relative_to_docs = "relative_to_docs"


class Nav(BaseModel):
    omitted_files: ValidationLevel | None = "info"
    not_found: ValidationLevel | None = "warn"
    absolute_links: ValidationLevel | None = "info"


class Links(BaseModel):
    not_found: ValidationLevel | None = "warn"
    anchors: ValidationLevel | None = "info"
    absolute_links: ValidationLevelForAbsolute | None = "info"
    unrecognized_links: ValidationLevel | None = "info"


class ValidationConfig(BaseModel):
    nav: Nav | None = None
    links: Links | None = None
    omitted_files: ValidationLevel | None = None
    not_found: ValidationLevel | None = None
    absolute_links: ValidationLevelForAbsolute | None = None
    anchors: ValidationLevel | None = None
    unrecognized_links: ValidationLevel | None = None
