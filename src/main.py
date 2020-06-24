import logging
import os
import sys
import logging_gelf.handlers
import logging_gelf.formatters
from lib.component import Component

# Environment setup
sys.tracebacklimit = 0

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-8s - %(filename)s : [line:%(lineno)3s] %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S")


if 'KBC_LOGGER_ADDR' in os.environ and 'KBC_LOGGER_PORT' in os.environ:

    logger = logging.getLogger()
    logging_gelf_handler = logging_gelf.handlers.GELFTCPSocketHandler(
        host=os.getenv('KBC_LOGGER_ADDR'),
        port=int(os.getenv('KBC_LOGGER_PORT'))
        )
    logging_gelf_handler.setFormatter(logging_gelf.formatters.GELFFormatter(null_character=True))
    logger.addHandler(logging_gelf_handler)

    # removes the initial stdout logging
    logger.removeHandler(logger.handlers[0])

# Key definition

APP_VERSION = '0.2.8'

if __name__ == '__main__':

    logging.info("Running app version %s..." % APP_VERSION)

    mngr = Component()
    mngr.run()

    logging.info("User management finished!")
