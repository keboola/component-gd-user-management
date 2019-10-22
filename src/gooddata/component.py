# import logging
from gooddata.client import UserManagementClient
from kbc.env_handler import KBCEnvHandler


KEY_USERNAME = 'username'
KEY_PASSWORD = '#password'
KEY_PROJECT_ID = 'pid'
KEY_CUSTOM_DOMAIN = 'domain_custom'
KEY_IMAGE_PROVISIONING_URL = 'provisioning_url'
KEY_IMAGE_GOODDATA_URL = 'gd_url'

MANDATORY_PARAMETERS = [KEY_USERNAME, KEY_PASSWORD, KEY_PROJECT_ID]


class UserManagementComponent(KBCEnvHandler):

    def __init__(self,):

        super().__init__(MANDATORY_PARAMETERS)
        self.validate_config(MANDATORY_PARAMETERS)

        self.paramUsername = self.cfg_params[KEY_USERNAME]
        self.paramPassword = self.cfg_params[KEY_PASSWORD]
        self.paramProjectId = self.cfg_params[KEY_PROJECT_ID]
        self.paramCustomDomain = self.cfg_params[KEY_CUSTOM_DOMAIN]
        self.paramStorageToken = self.get_storage_token()

        self.paramGooddataUrl = self.image_params[KEY_IMAGE_GOODDATA_URL]
        self.paramKeboolaUrl = self.image_params[KEY_IMAGE_PROVISIONING_URL]

        self.client = UserManagementClient(username=self.paramUsername, password=self.paramPassword,
                                           projectId=self.paramProjectId, gooddataUrl=self.paramGooddataUrl,
                                           keboolaUrl=self.paramKeboolaUrl, storageToken=self.paramStorageToken)
