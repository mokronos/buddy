import logging
import os

debug_flag = os.environ.get("DEBUG", "0")
debug_level = logging.DEBUG if debug_flag == "1" else logging.INFO

logger = logging.getLogger("BUDDY")
logger.setLevel(debug_level)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(debug_level)
    handler.setFormatter(logging.Formatter("%(name)s|%(levelname)s: %(message)s"))

    logger.addHandler(handler)

logger.propagate = False

logger.debug("DEBUG LOGGING ENABLED")
