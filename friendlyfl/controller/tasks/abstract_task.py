import json
from abc import ABC, abstractmethod
import os
import requests
from django.http import HttpResponse
from dotenv import load_dotenv
import logging

# take environment variables from .env.
load_dotenv()
logger = logging.getLogger(__name__)

# read vars from env
site_uid = os.getenv('SITE_UID')
router_url = os.getenv('ROUTER_URL')
router_username = os.getenv('ROUTER_USERNAME')
router_password = os.getenv('ROUTER_PASSWORD')


class AbstractTask(ABC):
    """
    Abstract Class of a Task.
    All FL tasks should inherit this class and override the abstract methods defined.
    """

    run_id = ""
    config = ""
    last_round = False
    artifact = None

    def __init__(self, run_id, config):
        self.run_id = run_id
        self.config = config

    """
    Initial Model Task
    """

    @staticmethod
    def initial_task(run_id, config):
        task = AbstractTask(run_id, config)
        return task

    def standby(self):
        """
        Status: Standby,2
        Next Status: Preparing,3
        Called when a task starts. Current participant will start to prepare the run.
        In this event, notify router.
        """
        self.notify(3)

    def preparing(self):
        """
        Status: Preparing,3
        Next Status: Running,4;Pending Failed,1
        Called when a task starts. Current participant will start to prepare the run.
        In this event, input data files are validated.
        """
        valid = self.validate()
        if valid:
            self.notify(4)
        else:
            self.notify(1)

    def running(self):
        """
        Status: Running,4
        Next Status: Pending Success,5;Pending Failed,1
        Called when all participants have prepared to run.
        In this event, input data files are used for training.
        """
        valid = self.training()
        if valid:
            self.notify(4)
        else:
            self.notify(1)

    def pending_success(self):
        """
        Status: Pending Success,5
        Next Status: Success,6
        Called when current participant successfully completes the task.
        In this event, output file and logs will be uploaded to RS for forwarding to Coordinator.
        """
        if self.upload():
            self.notify(6)

    def pending_failed(self):
        """
        Status: Pending Failed,1
        Next Status: Failed,0
        Called when current participant fails to complete the task.
        In this event, logs will be uploaded to RS for forwarding to Coordinator.
        """
        if self.upload():
            self.notify(0)

    @abstractmethod
    def validate(self) -> bool:
        return True

    @abstractmethod
    def training(self) -> bool:
        return True

    def upload(self) -> bool:
        if self.artifact:
            return True
        else:
            return False

    def notify(self, next_state, param=None):
        if param is None:
            param = {}
        headers = {'Content-type': 'application/json'}
        data = dict()
        data['status'] = next_state
        requests.put('{0}/runs/{1}/status/'.format(router_url, self.run_id),
                     headers=headers,
                     auth=(router_username, router_password),
                     data=json.dumps(data))
