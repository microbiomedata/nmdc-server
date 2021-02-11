from celery import Celery

from nmdc_server.config import settings


celery_app = Celery("nmdc", backend=settings.celery_backend, broker=settings.celery_broker)
celery_app.conf.imports += ("nmdc_server.jobs",)
