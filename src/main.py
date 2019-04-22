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
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)-8s : [line:%(lineno)3s] %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S")


logger = logging.getLogger()
logging_gelf_handler = logging_gelf.handlers.GELFTCPSocketHandler(
    host=os.getenv('KBC_LOGGER_ADDR'),
    port=int(os.getenv('KBC_LOGGER_PORT'))
    )
logging_gelf_handler.setFormatter(logging_gelf.formatters.GELFFormatter(null_character=True))
logger.addHandler(logging_gelf_handler)

# removes the initial stdout logging
logger.removeHandler(logger.handlers[0])

# Access the supplied rules

GD_USERNAME = 'username'
GD_PASSWORD = '#password'
GD_PID = 'pid'
GD_CUSTOM_DOMAIN = 'domain_custom'
GD_URL = 'gd_url'
KBC_URL = 'provisioning_url'

MANDATORY_PARS = [GD_USERNAME, GD_PASSWORD, GD_PID, GD_CUSTOM_DOMAIN]

# logging.info("Successfully fetched all parameters.")

if __name__ == '__main__':

    mngr = Component(GD_USERNAME,
                     GD_PASSWORD,
                     GD_PID,
                     GD_CUSTOM_DOMAIN,
                     GD_URL,
                     KBC_URL,
                     MANDATORY_PARS)

    mngr.run()
