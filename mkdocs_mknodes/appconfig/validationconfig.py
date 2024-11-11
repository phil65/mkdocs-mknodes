from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


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
    nav: Nav = Field(default_factory=Nav)
    links: Links = Field(default_factory=Links)
    omitted_files: ValidationLevel = ValidationLevel.info
    not_found: ValidationLevel = ValidationLevel.warn
    absolute_links: ValidationLevelForAbsolute = ValidationLevelForAbsolute.info
    anchors: ValidationLevel = ValidationLevel.info
    unrecognized_links: ValidationLevel = ValidationLevel.info
