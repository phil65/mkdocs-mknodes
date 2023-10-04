from __future__ import annotations

import logging


class RichState:
    """Maintain logging level."""

    LOG_NAME = "mkdocs"

    def __init__(self, log_name: str | None = None, level: int = logging.INFO):
        """Constructor.

        Arguments:
            log_name: Logger name
            level: Logging level
        """
        from rich.logging import RichHandler

        self.logger = logging.getLogger(log_name or self.LOG_NAME)
        # Don't restrict level on logger; use handler
        self.logger.setLevel(1)
        self.logger.propagate = False
        self.stream = RichHandler(
            level,
            markup=False,
            rich_tracebacks=True,
            omit_repeated_times=False,
        )
        self.stream.name = "MkNodesStreamHandler"
        self.logger.addHandler(self.stream)

    def __del__(self):
        self.logger.removeHandler(self.stream)
