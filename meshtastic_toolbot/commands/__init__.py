from .ping import PingCommand
from .status import StatusCommand

COMMAND_REGISTRY = {
    "/ping": PingCommand,
    "/status": StatusCommand
}
