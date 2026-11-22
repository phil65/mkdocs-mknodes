from __future__ import annotations

import logfire


# from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor
# from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
# from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
# from opentelemetry.instrumentation.urllib import URLLibInstrumentor


def setup_logfire():
    code_source = logfire.CodeSource(
        repository="https://github.com/phil65/mkdocs-mknodes",
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
    # logfire.instrument_aiohttp_client()
    # logfire.instrument_httpx()
    # logfire.install_auto_tracing("mkdocs")

    # litellm.success_callback = ["logfire"]
    # litellm.callbacks = ["logfire"]
