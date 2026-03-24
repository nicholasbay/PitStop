import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parents[1] / 'logs' / 'pitstop.log'

def setup_logging():
    root_logger = logging.getLogger()

    # Prevent duplicate handlers when the app reloads in development.
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.DEBUG)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        LOG_PATH,
        when='midnight',
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
