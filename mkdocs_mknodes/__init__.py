__version__ = "0.4.9"


from .mkdefaultwebsite import MkDefaultWebsite
from . import telemetry

telemetry.setup_logfire()

__all__ = ["MkDefaultWebsite"]
