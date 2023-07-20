from abc import ABC, abstractmethod


class AbstractTask(ABC):
    """
    Abstract Class of a Task.
    All FL tasks should inherit this class and override the abstract methods defined.
    """
    @abstractmethod
    def preparing(self):
        """
        Called when a task starts. Current participant will start to prepare the run.
        In this event, input data files are validated.
        """
        pass

    @abstractmethod
    def running(self):
        """
        Called when all participants have prepared to run.
        In this event, input data files are used for training.
        """
        pass

    @abstractmethod
    def pending_success(self):
        """
        Called when current participant successfully completes the task.
        In this event, output file and logs will be uploaded to RS for forwarding to Coordinator.
        """
        pass

    @abstractmethod
    def pending_failed(self):
        """
        Called when current participant fails to complete the task.
        In this event, logs will be uploaded to RS for forwarding to Coordinator.
        """
        pass

    @abstractmethod
    def success(self):
        """
        Called when all participants have successfully completed the task.
        In this event, clean-ups can be done to wrap up the local task.
        """
        pass

    @abstractmethod
    def failed(self):
        """
        Called when run fails due to any reason.
        In this event, clean-ups can be done to wrap up the local task.
        """
        pass
