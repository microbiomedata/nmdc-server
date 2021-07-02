from logging import Logger, getLogger

from celery import current_task
from celery.utils.log import get_task_logger


def get_logger(name: str) -> Logger:
    if current_task:
        return get_task_logger(name)
    return getLogger(name)
