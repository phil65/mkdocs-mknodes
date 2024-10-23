from __future__ import annotations

from collections.abc import MutableMapping
import logging
from typing import Any

import logfire


# from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor
# from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
# from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
# from opentelemetry.instrumentation.urllib import URLLibInstrumentor


def setup_logfire():
    code_source = logfire.CodeSource(
        repository="https://github.com/phil65/mkdocs_mknodes",
        revision="main",
        root_path=".",
    )
    # console_opts = logfire.ConsoleOptions()
    logfire.configure(
        code_source=code_source,
        console=False,
        send_to_logfire="if-token-present",
        service_name="mkdocs-mknodes",
    )
    # logger = logging.getLogger("mkdocs")
    # handler = logfire.LogfireLoggingHandler()
    # handler.setLevel(logging.DEBUG)
    # logger.addHandler(handler)
    # logging.basicConfig(level=logging.DEBUG)
    # logger.setLevel(logging.DEBUG)
    # Jinja2Instrumentor().instrument()
    # SQLite3Instrumentor().instrument()
    # URLLib3Instrumentor().instrument()
    # URLLibInstrumentor().instrument()
    logfire.instrument_requests()
    logfire.instrument_system_metrics()
    logfire.instrument_aiohttp_client()
    # logfire.instrument_httpx()
    # logfire.install_auto_tracing("mkdocs")

    # litellm.success_callback = ["logfire"]
    # litellm.callbacks = ["logfire"]


class PrefixedLogger(logging.LoggerAdapter):
    """A logger adapter to prefix log messages."""

    def __init__(self, prefix: str, logger: logging.Logger) -> None:
        """Initialize the logger adapter.

        Arguments:
            prefix: The string to insert in front of every message.
            logger: The logger instance.
        """
        super().__init__(logger, {})
        self.prefix = prefix

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, Any]:
        """Process the message.

        Arguments:
            msg: The message:
            kwargs: Remaining arguments.

        Returns:
            The processed message.
        """
        return f"{self.prefix}: {msg}", kwargs


def get_plugin_logger(name: str) -> PrefixedLogger:
    """Return a logger for plugins.

    Arguments:
        name: The name to use with `logging.getLogger`.

    Returns:
        A logger configured to work well in MkDocs,
            prefixing each message with the plugin package name.

    Example:
        ```python
        from mkdocs.plugins import get_plugin_logger

        log = get_plugin_logger(__name__)
        log.info("My plugin message")
        ```
    """
    logger = logging.getLogger(f"mkdocs.plugins.{name}")
    logger.addHandler(logfire.LogfireLoggingHandler())
    return PrefixedLogger(name.split(".", 1)[0], logger)
