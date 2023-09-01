import json
import re
import time
from importlib import import_module


def epoch_time_in_sec():
    return int(time.time())


def load_class(module_name, class_name):
    module = import_module(module_name)
    klass = getattr(module, class_name)
    return klass


def camel_to_snake(name):
    return re.sub('(?!^)([A-Z]+)', r'_\1', name).lower()


def parse_tasks(tasks_str):
    if not tasks_str or tasks_str == '{}':
        return None
    try:
        return json.loads(tasks_str)
    except json.JSONDecodeError:
        return None


def format_status(status):
    """
    Example: Pending Aggregating -> pending_aggregating
    :param status: status with space
    :return: status with underscore
    """
    return status.replace(" ", "_").lower() if status else None
