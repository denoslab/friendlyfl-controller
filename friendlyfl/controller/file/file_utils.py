import logging
import tempfile
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

base_folder = '/friendlyfl-controller/local'

logs_name = 'logs.txt'

mid_artifacts_name = 'mid-artifacts.txt'

mid_artifacts_dir = 'all-mid-artifacts'

artifacts_name = 'artifacts.txt'


def create_if_not_exist(url):
    if url:
        try:
            file_path = Path(url)
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
        except Exception as e:
            logger.warning(
                "Error while creating log file: {} due to".format(e))


def gen_url(run_id, task_seq, round_seq, file_name):
    if not run_id or not task_seq or not round_seq:
        return None
    return f"{base_folder}/{run_id}/{task_seq}/{round_seq}/{file_name}"


def gen_logs_url(run_id, task_seq, round_seq):
    return gen_url(run_id, task_seq, round_seq, logs_name)


def gen_artifacts_url(run_id, task_seq, round_seq):
    return gen_url(run_id, task_seq, round_seq, artifacts_name)


def gen_mid_artifacts_url(run_id, task_seq, round_seq):
    return gen_url(run_id, task_seq, round_seq, mid_artifacts_name)


def gen_all_mid_artifacts_url(project_id, batch):
    if not project_id or not batch:
        return None
    return f"{base_folder}/{mid_artifacts_dir}/{project_id}/{batch}/"


def save_all_mid_artifacts(project_id, batch, content):
    dir_url = gen_all_mid_artifacts_url(project_id, batch)
    if dir_url:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
        file_path = Path(dir_url)
        file_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
            zip_ref.extractall(file_path)
        return file_path.absolute()
    return None


def read_file_from_url(url):
    if url:
        try:
            file_obj = open(url, 'r')
            return file_obj
        except FileNotFoundError:
            print(f"File not found at {url}")
            return None
    return None
