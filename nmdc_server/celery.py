import logging
import sys

from celery import Celery
from celery.signals import after_setup_logger
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from nmdc_server.config import settings


@after_setup_logger.connect()
def logger_setup_handler(logger, **kwargs):
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    logger.setLevel(logging.INFO)


celery_app = Celery("nmdc", backend=settings.celery_backend, broker=settings.celery_broker)
celery_app.conf.imports += ("nmdc_server.jobs",)


if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[CeleryIntegration(), RedisIntegration(), SqlalchemyIntegration()],
    )
