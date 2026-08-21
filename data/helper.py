
import logging
import os
import re
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


def check_if_pred_exist(pred_dir: str, retrieval_date: str, str_contain: str = '') -> str:
    """Check if prediction file for the given retrieval date already exists."""
    pred_files = [f for f in os.listdir(pred_dir) if f.endswith('.csv')]
    for f in pred_files:
        if retrieval_date in f and str_contain in f:
            return os.path.join(pred_dir, f)
    return ""


def is_same_title(title1: str, title2: str) -> bool:
    title1 = title1.strip().lower()
    title2 = title2.strip().lower()

    if title1 == title2:
        return True
    if title1.startswith(title2) or title2.startswith(title1):
        return True
    return False


def format_author_citation(author_str: str) -> str:
    """
    Formats an author string or stringified list into inline citations:
    - 1 author  -> "Lastname"
    - 2 authors -> "Lastname1 & Lastname2"
    - 3+ authors-> "Lastname1 et al."
    """
    if not author_str:
        return ""

    # Clean stringified list brackets/quotes: "['A', 'B']" -> "A, B"
    cleaned_str = re.sub(r"[\[\]'\"\]]", "", author_str)

    last_names = []
    for author in cleaned_str.split(","):
        author = author.strip()
        if not author:
            continue
        # Extract the last name (last sequence of letters/hyphens in each author segment)
        match = re.search(r'([A-Za-z\-]+)\s*$', author)
        if match:
            last_names.append(match.group(1))

    count = len(last_names)

    if count == 0:
        return ""
    if count == 1:
        return last_names[0]
    if count == 2:
        return f"{last_names[0]} & {last_names[1]}"
    return f"{last_names[0]} et al."
