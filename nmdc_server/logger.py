from logging import Logger, getLogger


def get_logger(name: str) -> Logger:
    """Returns the logger having the specified name."""
    return getLogger(name)
