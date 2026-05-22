import sys
import logging

def setup_unicode():
    """Reconfigure stdout/stderr to support Unicode characters in Windows terminal."""
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if sys.stderr.encoding != 'utf-8':
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

def get_logger(name: str) -> logging.Logger:
    """Create a standardized logger for RAG operations."""
    setup_unicode()
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
