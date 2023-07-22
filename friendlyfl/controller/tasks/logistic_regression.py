from friendlyfl.controller.tasks.abstract_task import AbstractTask


class LogisticRegression(AbstractTask):
    def __init__(self, run_id, config):
        super().__init__(run_id, config)

    def validate(self) -> bool:
        return True

    def training(self) -> bool:
        return True
