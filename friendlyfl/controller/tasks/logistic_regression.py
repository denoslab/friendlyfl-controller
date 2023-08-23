from friendlyfl.controller.tasks.abstract_task import AbstractTask


class LogisticRegression(AbstractTask):

    def __init__(self, run):
        super().__init__(run)

    def validate(self) -> bool:
        return True

    def training(self) -> bool:
        return True

    def do_aggregate(self) -> bool:
        return True

    def download_artifacts(self) -> bool:
        return True
