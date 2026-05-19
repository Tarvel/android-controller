import logging
import sys

LOGGER = logging.getLogger("acc")

_FORMAT = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
)


def setup(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    LOGGER.setLevel(level)
    if not LOGGER.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(_FORMAT)
        LOGGER.addHandler(h)
