from importlib import import_module
import re


def load_class(module_name, class_name):
    module = import_module(module_name)
    klass = getattr(module, class_name)
    return klass


def camel_to_snake(name):
    return re.sub('(?!^)([A-Z]+)', r'_\1', name).lower()
