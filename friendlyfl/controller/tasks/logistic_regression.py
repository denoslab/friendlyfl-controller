from friendlyfl.controller.tasks.abstract_task import AbstractTask
from typing import Tuple, Union, List
import numpy as np
import openml
import logging
import sklearn.linear_model

logger = logging.getLogger(__name__)

XY = Tuple[np.ndarray, np.ndarray]
Dataset = Tuple[XY, XY]
LogRegParams = Union[XY, Tuple[np.ndarray]]
XYList = List[XY]


def load_mnist() -> Dataset:
    """
    Loads the MNIST dataset using OpenML.
    OpenML dataset link: https://www.openml.org/d/554
    """
    mnist_openml = openml.datasets.get_dataset(554)
    Xy, _, _, _ = mnist_openml.get_data(dataset_format="array")
    X = Xy[:, :-1]  # the last column contains labels
    y = Xy[:, -1]
    # First 60000 samples consist of the train set
    x_train, y_train = X[:60000], y[:60000]
    x_test, y_test = X[60000:], y[60000:]
    return (x_train, y_train), (x_test, y_test)


class LogisticRegression(AbstractTask):

    def __init__(self, run):
        super().__init__(run)
        self.logisticRegr = None
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None
        # load dataset
        logger.warning('Loading MNIST dataset...')
        (self.X_train, self.y_train), (self.X_test, self.y_test) = load_mnist()
        logger.warning(f'Training data shape: {self.X_train.shape}')
        logger.warning(f'Training label shape: {self.y_train.shape}')

    def validate(self) -> bool:
        """
        This step is used to load and validate the input data.
        """

        return True

    def training(self) -> bool:
        """
        This step is used for training.
        all parameters not specified are set to their defaults
        default solver is incredibly slow thats why we change it
        """

        self.logisticRegr = sklearn.linear_model.LogisticRegression(
            penalty="l2",
            max_iter=1,  # local epoch
            warm_start=True,  # prevent refreshing weights when fitting
        )
        logger.warning('Starting training...')
        self.logisticRegr.fit(self.X_train, self.y_train)
        score = self.logisticRegr.score(self.X_test, self.y_test)
        logger.warning(f'Training complete. Model score: {score}')
        return True

    def do_aggregate(self) -> bool:
        return True

    def download_artifacts(self) -> bool:
        return True
