import json
import os
import requests
from celery import Celery
from celery.utils.log import get_task_logger
from kombu import Exchange, Queue
from friendlyfl.controller import redis
from friendlyfl.controller.site_status_task import report_alive
from friendlyfl.controller.utils import load_class, camel_to_snake, format_status

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

router_url = os.getenv('ROUTER_URL')
router_username = os.getenv('ROUTER_USERNAME')
router_password = os.getenv('ROUTER_PASSWORD')
site_id = os.getenv('SITE_UID')

run_key = 'friendlyfl:controller:run:list:'


@app.task(bind=True, queue='friendlyfl.run', name='fetch_run')
def fetch_run(args):
    """
    Fetch run status based on site_id, cache it and notify processor.
    :return:
    """
    logger.debug("Received: {}".format(args))

    runs = check_status_change(site_id)
    if runs:
        for run in runs:
            process_task.s(run, False).apply_async(
                queue='friendlyfl.processor')


@app.task(bind=True, queue='friendlyfl.run', name='monitor_run')
def monitor_run(args):
    """
    Monitor coordinator run in waiting status
    :param args:
    :return:
    """
    run_list = fetch()
    if run_list:
        retry_run = []
        for r in run_list:
            if r['site_uid'] == site_id and r['role'] == 'coordinator':
                exist_run = get_run_from_redis(r)
                if exist_run:
                    run = json.loads(exist_run)
                    # TODO: Check waiting status: preparing, pending aggregating
                    if r['status'] == run['status'] and True:
                        retry_run.append(r)

        if retry_run:
            for run in retry_run:
                process_task.s(run, True).apply_async(
                    queue='friendlyfl.processor')


@app.task(bind=True, queue='friendlyfl.run', name='site_heartbeat')
def heartbeat(args):
    report_alive()


@app.task(bind=True, queue='friendlyfl.processor', name='process_task')
def process_task(args, run, is_retry):
    """
    :param args:
    :param run: run model
    :param is_retry: whether the task is triggered by retry
    :return:
    """
    logger.debug("Received: {} options: {}".format(args, run))
    cur_seq = run['cur_seq']
    tasks = run['tasks']
    model = tasks[cur_seq - 1]['model']
    status = run['status']
    logger.debug("Model: {}".format(model))
    try:
        klass = load_class('friendlyfl.controller.tasks.{}'.format(
            camel_to_snake(model)), model)
        logger.debug("Class: {}".format(klass))
        instance = klass(run)
        instance.method_call(format_status(status))

    except (ImportError, AttributeError) as e:
        logger.warn("{} not found with error: {}".format(model, e))


def fetch():
    headers = {'Content-type': 'application/json'}
    data = dict()
    response = requests.get('{0}/runs/active/'.format(router_url),
                            headers=headers,
                            auth=(router_username, router_password),
                            data=json.dumps(data))
    if response.ok:
        return response.json()
    else:
        return None


def check_status_change(site_id) -> []:
    """
    Check run status to decide whether send message to task processor
    :return:
    """
    run_list = fetch()
    if run_list:
        changed_run = []
        for r in run_list:
            if r['site_uid'] == site_id:
                exist_run = get_run_from_redis(r)
                if exist_run:
                    run = json.loads(exist_run)
                    if r['status'] != run['status']:
                        changed_run.append(r)
                        add_to_redis(r)
                else:
                    changed_run.append(r)
                    add_to_redis(r)
        return changed_run
    return None


def get_run_from_redis(run):
    r = redis.get_redis()
    return r.get(run_key + str(run['id']))


def add_to_redis(run):
    logger.debug(json.dumps(run))
    r = redis.get_redis()
    k = run_key + str(run['id'])
    r.set(k, json.dumps(run), ex=86400)


def reset_cache():
    r = redis.get_redis()
    r.delete(run_key)


reset_cache()
app.autodiscover_tasks()
