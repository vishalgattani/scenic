import logging
REFRESH = False

logger = logging.getLogger(__name__)
level = logging.INFO
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
formatter = logging.Formatter('[%(levelname)s] - %(message)s (%(lineno)d)')
ch.setFormatter(formatter)
logger.addHandler(ch)

if __name__ == "__main__":
    logger.info("Generating Scene")


