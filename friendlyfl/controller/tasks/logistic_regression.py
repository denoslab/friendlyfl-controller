import json

from friendlyfl.controller.file.file_utils import gen_mid_artifacts_url
from friendlyfl.controller.tasks.abstract_task import AbstractTask
import sklearn.linear_model
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
import warnings
warnings.filterwarnings('ignore')


class LogisticRegression(AbstractTask):

    def __init__(self, run):
        super().__init__(run)
        self.logisticRegr = None
        self.X_train_scaled = None
        self.y_train = None
        self.X_test_scaled = None
        self.y_test = None

    def prepare_data(self) -> bool:
        # load dataset
        self.logger.debug('Loading dataset for run {} ...'.format(self.run_id))
        X, y = self.read_dataset(self.run_id)
        if X is not None and len(X) > 0 and y is not None and len(y) > 0:
            # Split the data into training and testing sets
            X_train, X_test, self.y_train, self.y_test = train_test_split(
                X, y, test_size=0.2, random_state=42)

            # Standardize the numerical features
            scaler = StandardScaler()
            self.X_train_scaled = scaler.fit_transform(X_train)
            self.X_test_scaled = scaler.transform(X_test)
            self.logger.debug(
                f'Training data shape: {self.X_train_scaled.shape}')
            self.logger.debug(f'Training label shape: {self.y_train.shape}')
            self.logger.debug(f'Test data shape: {self.X_test_scaled.shape}')
            self.logger.debug(f'Test label shape: {self.y_test.shape}')

            # Initialize Logistic regression model
            self.logisticRegr = sklearn.linear_model.LogisticRegression(
                penalty="l2",
                max_iter=1,  # local epoch
                warm_start=True,  # prevent refreshing weights when fitting
            )
            return True
        else:
            self.logger.warning("Data set is not ready")
        return False

    def validate(self) -> bool:
        """
        This step is used to load and validate the input data.
        """
        task_round = self.get_round()
        validate_log = "Run {} - task -{} - round {} task begins".format(
            self.run_id, self.cur_seq, task_round)
        self.logger.debug(validate_log)

        return True

    def training(self) -> bool:
        """
        This step is used for training.
        all parameters not specified are set to their defaults
        default solver is incredibly slow thats why we change it
        """

        self.logger.info('Starting training...')
        self.logisticRegr.fit(self.X_train_scaled, self.y_train)
        score = self.logisticRegr.score(self.X_test_scaled, self.y_test)
        self.logger.info(f'Training complete. Model score: {score}')
        y_predict = self.logisticRegr.predict(self.X_test_scaled)

        # Accuracy metric
        accuracy = accuracy_score(self.y_test, y_predict)
        self.logger.info(f'Accuracy: {accuracy}')
        report = classification_report(self.y_test, y_predict)
        self.logger.info(f'Classification report : \n  {report}')

        # Documentation: https://scikit-learn.org/stable/modules/model_evaluation.html
        # ROC-AUC
        auc = roc_auc_score(self.y_test, y_predict)
        self.logger.info(f'AUC: {auc}')

        # Use confusion matrix to calculate the metrics
        tn, fp, fn, tp = confusion_matrix(self.y_test, y_predict).ravel()

        accuracy = (tp + tn) / (tn + fp + fn + tp)
        self.logger.info(f'Accuracy: {accuracy}')

        sensitivity = tp / (tp + fn)
        self.logger.info(f'Sensitivity: {sensitivity}')

        specificity = tn / (tn + fp)
        self.logger.info(f'Specificity: {specificity}')

        npv = tn / (tn + fn)
        self.logger.info(f'NPV: {npv}')

        ppv = tp / (tp + fp)
        self.logger.info(f'PPV: {ppv}')

        to_upload = {
            "coef_": self.logisticRegr.coef_.tolist(),
            "intercept_": self.logisticRegr.intercept_.tolist(),
            "metric_acc": accuracy,
            "metric_auc": auc,
            "metric_sensitivity": sensitivity,
            "metric_specificity": specificity,
            "mertic_npv": npv,
            "metric_ppv": ppv
        }

        self.logger.info(to_upload)
        return self.add_mid_artifacts(json.dumps(to_upload))

    def do_aggregate(self) -> bool:
        # TODO: download the intermedia model files
        # (this should be a list with intermediate model payloads from all clients)
        # downloaded = {
        #     "coef_": self.logisticRegr.coef_,
        #     "intercept_": self.logisticRegr.intercept_,
        #     "metric_acc": accuracy,
        #     "metric_auc": auc,
        #     "metric_sensitivity": sensitivity,
        #     "metric_specificity": specificity,
        #     "mertic_npv": npv,
        #     "metric_ppv": ppv
        # }
        # aggregation logic for coordinator

        return True
