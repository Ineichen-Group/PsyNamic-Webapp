
import os
import logging
from datetime import datetime, timedelta

def cleanup_old_logs(log_dir: str, keep_n: int = 50):
    """Deletes old log files, keeping only the N most recent ones."""
    try:
        log_files = [f for f in os.listdir(log_dir) if f.startswith(
            'predict_') and f.endswith('.log')]
        if len(log_files) <= keep_n:
            return

        # Sort files by creation time (embedded in filename)
        log_files.sort(key=lambda x: datetime.strptime(
            x.split('_')[1], "%Y%m%d"), reverse=True)

        # Files to delete
        files_to_delete = log_files[keep_n:]

        for f in files_to_delete:
            os.remove(os.path.join(log_dir, f))
            logging.info(f"Removed old log file: {f}")

    except Exception as e:
        logging.warning(f"Could not clean up old logs: {e}")


def format_timedelta_hms(td: timedelta) -> str:
    """Format timedelta to HH-MM-SS string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}-{minutes:02d}-{seconds:02d}"


def check_if_pred_exist(pred_dir: str, retrieval_date: str, str_contain: str='') -> str:
    """Check if prediction file for the given retrieval date already exists."""
    pred_files = [f for f in os.listdir(pred_dir) if f.endswith('.csv')]
    for f in pred_files:
        if retrieval_date in f and str_contain in f:
            return os.path.join(pred_dir, f)
    return ""
