from celery import Celery
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from nmdc_server.config import settings


celery_app = Celery("nmdc", backend=settings.celery_backend, broker=settings.celery_broker)
celery_app.conf.imports += ("nmdc_server.jobs",)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[CeleryIntegration(), RedisIntegration(), SqlalchemyIntegration()],
    )
