import inspect
import json
import logging
import os
from abc import ABC, abstractmethod

import requests
from dotenv import load_dotenv

from friendlyfl.controller.file.file_utils import append_logs, read_file_from_url, \
    gen_mid_artifacts_url, gen_logs_url
from friendlyfl.controller.utils import format_status


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
    project_id = None
    run_id = None
    batch_id = None
    cur_seq = None
    tasks = None
    role = None
    artifact = None
    status = None

    def __init__(self, run):
        self.project_id = run['project']
        self.run_id = run['id']
        self.batch_id = run['batch']
        self.role = run['role']
        self.tasks = run['tasks']
        self.cur_seq = run['cur_seq']
        self.status = run['status']

    def method_call(self, name: str, *args, **kwargs):
        if hasattr(self, name) and callable(getattr(self, name)):
            func = getattr(self, name)
            func(*args, **kwargs)
        else:
            logger.warning("method {} not exists".format(name))

    def standby(self, *args, **kwargs):
        """
        Status: Standby,2
        Next Status: Preparing,3;Pending Failed,1
        Called when a task starts. Current participant will start to prepare the run.
        In this event, notify router.
        """
        try:
            run = args[0]
            self.cur_seq = run['cur_seq']
            self.tasks = run['tasks']
            s = inspect.currentframe().f_code.co_name
            if self.status == s:
                logger.warning(
                    "Already in status {}. Ignore message".format(s))
                return
            else:
                self.status = s
            valid = self.validate()
            if valid:
                self.notify(3)
            else:
                self.notify(1)
        except Exception as e:
            logger.warning("Exception in standby status: {}".format(e))
            self.notify(1)

    def preparing(self, *args, **kwargs):
        """
        Status: Preparing,3
        Next Status: Running,4; Pending Failed,1
        Called when a task starts. Current participant will start to prepare the run.
        In this event, input data files are validated.
        """
        try:
            s = inspect.currentframe().f_code.co_name
            if self.role == 'coordinator':
                self.status = s
                if self.runs_in_fails():
                    self.notify(1)
                    return
                if self.runs_in_same_state('preparing'):
                    self.notify(4)
            else:
                if self.status == s:
                    logger.warning(
                        "Already in status {}. Ignore message".format(s))
                    return
                else:
                    self.status = s
        except Exception as e:
            logger.warning("Exception in preparing status: {}".format(e))

    def running(self, *args, **kwargs):
        """
        Status: Running,4
        Next Status: Pending Success,5;Pending Failed,1
        Called when all participants have prepared to run.
        In this event, input data files are used for training.
        """
        try:
            s = inspect.currentframe().f_code.co_name
            if self.status == s:
                logger.warning(
                    "Already in status {}. Ignore message".format(s))
                return
            else:
                self.status = s

            valid = self.training()
            if valid:
                self.notify(5)
            else:
                self.notify(1)
        except Exception as e:
            logger.warning("Exception in running status: {}".format(e))

    def pending_success(self, *args, **kwargs):
        """
        Status: Pending Success,5
        Next Status: Pending Aggregating,6; Standby,2
        Called when current participant successfully completes the task.
        In this event, output file and file will be uploaded to RS for forwarding to Coordinator.
        """
        try:
            if self.upload():
                self.notify(6)
        except Exception as e:
            logger.warning("Exception in pending_success status: {}".format(e))

    def pending_aggregating(self, *args, **kwargs):
        """
        Status: Pending Aggregating, 6
        Next Status: Aggregating, 7; Failed, 0
        Participant: Do nothing
        Coordinator: Waiting for all participants been changed to this status and download the artifacts
        :return:
        """
        try:
            s = inspect.currentframe().f_code.co_name
            if self.role == 'coordinator':
                self.status = s
                if self.runs_in_fails():
                    self.notify(0)
                if self.runs_in_same_state('pending_aggregating') and self.download_artifacts():
                    self.notify(7)
            else:
                if self.status == s:
                    logger.warning(
                        "Already in status {}. Ignore message".format(s))
                    return
                else:
                    self.status = s
        except Exception as e:
            logger.warning(
                "Exception in pending aggregating status: {}".format(e))

    def aggregating(self, *args, **kwargs):
        """
        Status: Aggregating, 7
        Next Status: Standby,2; Success,8; Failed,0
        Participant: Do nothing
        Coordinator: Aggregate artifacts from all participants and upload the final artifact.
        :return:
        """
        try:
            s = inspect.currentframe().f_code.co_name
            if self.role == 'coordinator':
                self.status = s
                if self.runs_in_fails():
                    self.notify(0)
                if self.do_aggregate():
                    is_last_round = self.is_last_round()
                    logger.debug("Is the last round? {}".format(is_last_round))
                    if is_last_round:
                        self.notify(8)
                    else:
                        self.notify(2, param={'increase_round': True})
                else:
                    self.notify(0)
            else:
                if self.status == s:
                    logger.warning(
                        "Already in status {}. Ignore message".format(s))
                    return
                else:
                    self.status = s
        except Exception as e:
            logger.warning("Exception in aggregating status: {}".format(e))

    def pending_failed(self, *args, **kwargs):
        """
        Status: Pending Failed,1
        Next Status: Failed,0
        Called when current participant fails to complete the task.
        In this event, file will be uploaded to RS for forwarding to Coordinator.
        """
        try:
            if self.upload():
                self.notify(0)
        except Exception as e:
            logger.warning("Exception in pending failed status: {}".format(e))

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
        # Here assume when round of task success, it should upload both mid-artifacts and logs to router
        task_round = self.get_round()
        if task_round:

            logger.warning('will upload logs and mid-artifacts')

            files_data = dict()
            data = dict()

            mid_artifacts_url = gen_mid_artifacts_url(
                self.run_id, self.cur_seq, task_round)
            logs_url = gen_logs_url(self.run_id, self.cur_seq, task_round)

            if mid_artifacts_url:
                files_data['mid_artifacts'] = read_file_from_url(
                    mid_artifacts_url)
            if logs_url:
                files_data['logs'] = read_file_from_url(logs_url)

            data['run'] = self.run_id
            data['task_seq'] = self.cur_seq
            data['round_seq'] = task_round
            if any(files_data.values()):
                response = requests.post('{0}/runs-action/upload/'.format(router_url, self.run_id),
                                         auth=(router_username,
                                               router_password),
                                         data=data,
                                         files=files_data)
                if response.status_code == 200:
                    logger.debug(
                        'Successfully upload logs and mid-artifacts of run {} - task {} - round {}'.format(self.run_id,
                                                                                                           self.cur_seq,
                                                                                                           task_round))
                    return True
            else:
                logger.debug("Files data is empty. Ignore upload")
                return True

        return False

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

    def runs_in_fails(self) -> bool:
        runs = self.fetch_runs()
        if runs:
            for r in runs:
                if format_status(r['status']) in ['pending_failed', 'failed']:
                    return True
        return False

    # This method can be used to append logs into local file system
    def add_logs(self, log):
        task_round = self.get_round()
        if round:
            append_logs(self.run_id, self.cur_seq, task_round, log)
        else:
            logger.debug("Failed to save logs since not round info found")

    # This method can be used to get current round of current task
    def get_round(self):
        if self.tasks and len(self.tasks) > 0:
            cur_task = self.tasks[self.cur_seq - 1]
            if cur_task and len(cur_task) > 0 and 'config' in cur_task:
                return cur_task['config']['current_round']
        return None
