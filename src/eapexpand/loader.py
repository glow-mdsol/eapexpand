from .models.loader import Enumeration, load_objects
import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_expanded_dir(source_dir: str):
    """
    Load the expanded EAP directory
    :param source_dir: Target source directory
    """
    # load the key entities
    objects = load_objects(source_dir)
    logger.info(f"Loaded {len(objects)} objects")
    return objects
