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

        # load dataset
        self.logger.warning('Loading breast_cancer dataset...')
        X, y = load_breast_cancer(return_X_y=True)
        # Split the data into training and testing sets
        X_train, X_test, self.y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Standardize the numerical features
        scaler = StandardScaler()
        self.X_train_scaled = scaler.fit_transform(X_train)
        self.X_test_scaled = scaler.transform(X_test)
        self.logger.warning(f'Training data shape: {self.X_train_scaled.shape}')
        self.logger.warning(f'Training label shape: {self.y_train.shape}')
        self.logger.warning(f'Test data shape: {self.X_test_scaled.shape}')
        self.logger.warning(f'Test label shape: {self.y_test.shape}')

        # Initialize Logistic regression model
        self.logisticRegr = sklearn.linear_model.LogisticRegression(
            penalty="l2",
            max_iter=1,  # local epoch
            warm_start=True,  # prevent refreshing weights when fitting
        )

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

        self.logger.warning('Starting training...')
        self.logisticRegr.fit(self.X_train_scaled, self.y_train)
        score = self.logisticRegr.score(self.X_test_scaled, self.y_test)
        self.logger.warning(f'Training complete. Model score: {score}')
        y_predict = self.logisticRegr.predict(self.X_test_scaled)

        # Accuracy metric
        accuracy = accuracy_score(self.y_test, y_predict)
        self.logger.warning(f'Accuracy: {accuracy}')
        report = classification_report(self.y_test, y_predict)
        self.logger.warning(f'Classification report : \n  {report}')

        # Documentation: https://scikit-learn.org/stable/modules/model_evaluation.html
        # ROC-AUC
        auc = roc_auc_score(self.y_test, y_predict)
        self.logger.warning(f'AUC: {auc}')

        # Use confusion matrix to calculate the metrics
        tn, fp, fn, tp = confusion_matrix(self.y_test, y_predict).ravel()

        accuracy = (tp + tn) / (tn + fp + fn + tp)
        self.logger.warning(f'Accuracy: {accuracy}')

        sensitivity = tp / (tp + fn)
        self.logger.warning(f'Sensitivity: {sensitivity}')

        specificity = tn / (tn + fp)
        self.logger.warning(f'Specificity: {specificity}')

        npv = tn / (tn + fn)
        self.logger.warning(f'NPV: {npv}')

        ppv = tp / (tp + fp)
        self.logger.warning(f'PPV: {ppv}')

        to_upload = {
            "coef_": self.logisticRegr.coef_,
            "intercept_": self.logisticRegr.intercept_,
            "metric_acc": accuracy,
            "metric_auc": auc,
            "metric_sensitivity": sensitivity,
            "metric_specificity": specificity,
            "mertic_npv": npv,
            "metric_ppv": ppv
        }
        # TODO: upload the dict "to_upload" as a file
        return True

    def do_aggregate(self) -> bool:
        # TODO: download the intermedia model files
        # (this should be a list with intermediate model payloads from all clients)
        downloaded = {
            "coef_": self.logisticRegr.coef_,
            "intercept_": self.logisticRegr.intercept_,
            "metric_acc": accuracy,
            "metric_auc": auc,
            "metric_sensitivity": sensitivity,
            "metric_specificity": specificity,
            "mertic_npv": npv,
            "metric_ppv": ppv
        }
        # aggregation logic for coordinator

        return True
