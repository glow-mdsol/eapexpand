from .models.loader import Enumeration, load_objects

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_expanded_dir(source_dir: str, prefix: str | None = None, name: str | None = None):
    """
    Load the expanded EAP directory
    :param source_dir: Target source directory
    """
    # load the key entities
    document = load_objects(source_dir, prefix, name)
    logger.info(f"Loaded {len(document.objects)} objects")
    return document
