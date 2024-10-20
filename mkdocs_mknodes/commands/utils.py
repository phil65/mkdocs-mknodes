"""The Mkdocs Plugin."""

from __future__ import annotations

from collections.abc import Callable
import functools
import logging
import time
from typing import TYPE_CHECKING, TypeVar

from mkdocs import utils
from mkdocs.exceptions import Abort, BuildError
from mkdocs.plugins import get_plugin_logger


if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig


logger = get_plugin_logger(__name__)


def count_warnings(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapped(config: MkDocsConfig, *args, **kwargs):
        start = time.monotonic()
        warning_counter = utils.CountHandler()
        warning_counter.setLevel(logging.WARNING)
        if config.strict:
            logging.getLogger("mkdocs").addHandler(warning_counter)
        result = fn(config, *args, **kwargs)
        counts = warning_counter.get_counts()
        if counts:
            msg = ", ".join(f"{v} {k.lower()}s" for k, v in counts)
            msg = f"Aborted with {msg} in strict mode!"
            raise Abort(msg)
        duration = time.monotonic() - start
        logger.info("Documentation built in %.2f seconds", duration)
        logging.getLogger("mkdocs").removeHandler(warning_counter)

        return result

    return wrapped


T = TypeVar("T")


def handle_exceptions(fn: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(fn)
    def wrapped(config: MkDocsConfig, *args, **kwargs) -> T:
        try:
            return fn(config, *args, **kwargs)
        except Exception as e:
            # Run `build_error` plugin events.
            config.plugins.on_build_error(error=e)
            if isinstance(e, BuildError):
                msg = "Aborted with a BuildError!"
                logger.exception(msg)
                raise Abort(msg) from e
            raise
        # finally:
        # logging.getLogger("mkdocs").removeHandler(warning_counter)

    return wrapped
