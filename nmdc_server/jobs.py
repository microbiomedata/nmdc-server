from nmdc_server.celery import celery_app


@celery_app.task
def ping():
    return True
