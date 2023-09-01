import logging
from pathlib import Path

logger = logging.getLogger(__name__)

base_folder = '/friendlyfl-controller/local'

logs_name = 'logs.txt'

mid_artifacts_name = 'mid-artifacts.txt'

artifacts_name = 'artifacts.txt'


def append_logs(run_id, task_seq, round_seq, log):
    try:
        url = gen_logs_url(run_id, task_seq, round_seq)
        if url:
            file_path = Path(url)
            if file_path.exists():
                # Open the file in append mode and write the content
                with file_path.open(mode='a') as file:
                    file.write(log + '\n')
            else:
                # Create a new file with the content
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Create the file
                file_path.touch()
                with file_path.open(mode='w') as file:
                    file.write(log + '\n')
    except Exception as e:
        logger.warning("Error while append log to file: {}".format(e))


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


def read_file_from_url(url):
    if url:
        try:
            file_obj = open(url, 'r')
            return file_obj
        except FileNotFoundError:
            print(f"File not found at {url}")
            return None
    return None
