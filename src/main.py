import logging
import os
import sys
import logging_gelf.handlers
import logging_gelf.formatters
from keboola import docker
from lib.component import componentRunner

# Environment setup
abspath = os.path.abspath(__file__)
script_path = os.path.dirname(abspath)
os.chdir(script_path)
sys.tracebacklimit = 0

# Logging

logging.basicConfig(
    level=logging.INFO,
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
GD_REGION = 'domain_region'
GD_CUSTOM_DOMAIN = 'domain_custom'
KBC_SAPI_TOKEN = '#sapi_token'
DEFAULT_DATA_FOLDER = '/data/'

try:
    cfg = docker.Config(DEFAULT_DATA_FOLDER)
    params = cfg.get_parameters()
    gd_username = params[GD_USERNAME]
    gd_password = params[GD_PASSWORD]
    gd_pid = params[GD_PID]
    sapi_token = params[KBC_SAPI_TOKEN]
    gd_region = params[GD_REGION]
    gd_custom_domain = params[GD_CUSTOM_DOMAIN]
except KeyError as e:
    logging.error("Parameter %s is missing. Please, provide the parameter and try again." % e)
    sys.exit(1)

logging.info("Successfully fetched all parameters.")

# Tables congig
in_tables = cfg.get_input_tables()

if __name__ == '__main__':

    mngr = componentRunner(gd_username,
                           gd_password,
                           gd_pid,
                           gd_region,
                           gd_custom_domain,
                           sapi_token,
                           DEFAULT_DATA_FOLDER,
                           in_tables)

    mngr.run()
