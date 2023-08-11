import os
from celery import Celery
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue

from friendlyfl.controller.tasks.site_status_task import report_alive
from friendlyfl.controller.utils import load_class, camel_to_snake

logger = get_task_logger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "friendlyfl.settings")
app = Celery("friendlyfl")
app.config_from_object("django.conf:settings", namespace="CELERY")

run_exchange = Exchange('friendlyfl.run', type='direct')
task_exchange = Exchange('friendlyfl.processor', type='direct')

app.conf.task_queues = {
    Queue('friendlyfl.run', run_exchange, routing_key='friendlyfl.run'),
    Queue('friendlyfl.processor', task_exchange,
          routing_key='friendlyfl.processor')
}


@app.task(bind=True, queue='friendlyfl.run', name='fetch_run')
def fetch_run(args):
    """
    TODO: Fetch run status based on site_id and keep the status.
    :return:
    """
    logger.debug("Received: {}".format(args))

    site_id = os.getenv('SITE_UID')
    logger.debug("Fetching runs by site_id: {}".format(site_id))
    process_task.s({'model': 'LogisticRegression'}).apply_async(
        queue='friendlyfl.processor')


@app.task(bind=True, queue='friendlyfl.run', name='site_heartbeat')
def heartbeat(args):
    report_alive()


@app.task(bind=True, queue='friendlyfl.processor', name='process_task')
def process_task(args, options):
    """
    TODO: Process task based on model. Need logic check and etc.
    :param args:
    :param options:
    :return:
    """
    logger.debug("Received: {} options: {}".format(args, options))
    model = options['model']
    logger.debug("Model: {}".format(model))
    try:
        klass = load_class('friendlyfl.controller.tasks.{}'.format(
            camel_to_snake(model)), model)
        logger.debug("Class: {}".format(klass))
        instance = klass(1, {})
        instance.standby()
    except (ImportError, AttributeError) as e:
        logger.warn("{} not found with error: {}".format(model, e))


app.autodiscover_tasks()
