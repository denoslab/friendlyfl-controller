import logging

from friendlyfl.controller.tasks.abstract_task import AbstractTask

logger = logging.getLogger(__name__)


class LogisticRegression(AbstractTask):

    def __init__(self, run):
        super().__init__(run)

    def validate(self) -> bool:
        task_round = self.get_round()
        validate_log = "Run {} - task -{} - round {} task begins".format(
            self.run_id, self.cur_seq, task_round)
        self.add_logs(validate_log)
        logger.debug(validate_log)
        return True

    def training(self) -> bool:
        return True

    def do_aggregate(self) -> bool:
        return True

    def download_artifacts(self) -> bool:
        return True
