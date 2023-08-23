import json
from abc import ABC, abstractmethod
import os
import requests
from dotenv import load_dotenv
import logging

# take environment variables from .env.
from friendlyfl.controller.utils import format_status

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
    project_id = None
    run_id = None
    batch_id = None
    cur_seq = None
    tasks = None
    role = None
    artifact = None

    def __init__(self, run):
        self.project_id = run['project']
        self.run_id = run['id']
        self.batch_id = run['batch']
        self.cur_seq = run['cur_seq']
        self.role = run['role']
        self.tasks = run['tasks']

    def method_call(self, name: str):
        if hasattr(self, name) and callable(getattr(self, name)):
            func = getattr(self, name)
            func()
        else:
            logger.warning("method {} not exists".format(name))

    def standby(self):
        """
        Status: Standby,2
        Next Status: Preparing,3;Pending Failed,1
        Called when a task starts. Current participant will start to prepare the run.
        In this event, notify router.
        """
        valid = self.validate()
        if valid:
            self.notify(3)
        else:
            self.notify(1)

    def preparing(self):
        """
        Status: Preparing,3
        Next Status: Running,4
        Called when a task starts. Current participant will start to prepare the run.
        In this event, input data files are validated.
        """
        if self.role == 'coordinator':
            if self.runs_in_same_state('preparing'):
                self.notify(4)
            # TODO: check failed

    def running(self):
        """
        Status: Running,4
        Next Status: Pending Success,5;Pending Failed,1
        Called when all participants have prepared to run.
        In this event, input data files are used for training.
        """
        valid = self.training()
        if valid:
            self.notify(5)
        else:
            self.notify(1)

    def pending_success(self):
        """
        Status: Pending Success,5
        Next Status: Pending Aggregating,6; Standby,2
        Called when current participant successfully completes the task.
        In this event, output file and logs will be uploaded to RS for forwarding to Coordinator.
        """
        if self.upload():
            self.notify(6)

    def pending_aggregating(self):
        """
        Status: Pending Aggregating, 6
        Next Status: Aggregating, 7
        Participant: Do nothing
        Coordinator: Waiting for all participants been changed to this status and download the artifacts
        :return:
        """
        if self.role == 'coordinator':
            if self.runs_in_same_state('pending_aggregating') and self.download_artifacts():
                self.notify(7)

    def aggregating(self):
        """
        Status: Aggregating, 7
        Next Status: Standby,2; Success,8; Failed,0
        Participant: Do nothing
        Coordinator: Aggregate artifacts from all participants and upload the final artifact.
        :return:
        """
        if self.role == 'coordinator':
            if self.do_aggregate():
                is_last_round = self.is_last_round()
                logger.debug("Is the last round? {}".format(is_last_round))
                if is_last_round:
                    self.notify(8)
                else:
                    self.notify(2, param={'increase_round': True})
            else:
                self.notify(0)

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

    @abstractmethod
    def download_artifacts(self) -> bool:
        """
        TODO: Download all artifacts for aggregating
        :return:
        """
        logger.debug("Downloading artifacts")
        return True

    @abstractmethod
    def do_aggregate(self) -> bool:
        """
        :return:
        """
        return True

    def upload(self) -> bool:
        return True

    def notify(self, next_state, param: dict = None):
        if param is None:
            param = dict()
        headers = {'Content-type': 'application/json'}
        param['status'] = next_state
        requests.put('{0}/runs/{1}/status/'.format(router_url, self.run_id),
                     headers=headers,
                     auth=(router_username, router_password),
                     data=json.dumps(param))

    def fetch_runs(self):
        runs_response = requests.get(
            '{0}/runs/detail/?batch={1}&project={2}&site_uid={3}'.format(
                router_url, self.batch_id, self.project_id, site_uid),
            auth=(router_username, router_password))
        if runs_response.ok:
            dic = runs_response.json()
            runs = dic['runs']
            return runs
        return None

    def is_last_round(self) -> bool:
        """
        Determine whether it is the last round.
        Logic:
        1. check tasks size vs the cur_seq
        2. check total_round and current_round inside tasks
        :return:
        """
        logger.debug(
            "Checking whether it is the last round. cur_seq: {}, tasks: {}".format(self.cur_seq, len(self.tasks)))
        if self.cur_seq >= len(self.tasks):
            c = self.tasks[self.cur_seq - 1]['config']
            if 'total_round' in c and 'current_round' in c:
                total_round = c['total_round']
                current_round = c['current_round']
                logger.debug("Total Round: {}, Current Round: {}".format(
                    total_round, current_round))
                return current_round >= total_round
            else:
                return True
        else:
            return False

    def runs_in_same_state(self, expected_state) -> bool:
        """
        Coordinator: Check all participants are in expected status
        :param expected_state:
        :return:
        """
        logger.debug("Checking whether all runs are in the same status")
        runs = self.fetch_runs()
        logger.debug("expected state: {}. All runs: {}".format(
            expected_state, runs))
        if runs:
            for r in runs:
                if format_status(r['status']) != expected_state:
                    return False
            return True
        else:
            return False
