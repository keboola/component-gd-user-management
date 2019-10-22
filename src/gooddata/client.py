import json
import logging
import os
# import re
import requests
import sys
# import secrets


class UserManagementClient:

    def __init__(self, username, password, projectId, gooddataUrl, keboolaUrl, storageToken):

        self.paramUsername = username
        self.paramPassword = password
        self.paramProjectId = projectId
        self.paramGooddataUrl = gooddataUrl
        self.paramKeboolaUrl = keboolaUrl
        self.paramStorageToken = storageToken

        logging.info("GoodData domain set to %s." % self.paramGooddataUrl)
        logging.info("Keboola domain set to %s." % self.paramKeboolaUrl)

        self._getSstToken()

    @staticmethod
    def _responseSplitter(responseObject):

        return responseObject.status_code, responseObject.json()

    def _getSstToken(self):

        dataSstReq = {
            'postUserLogin': {
                'login': self.paramUsername,
                'password': self.paramPassword,
                'remember': 1,
                'verify_level': 2
            }
        }

        headerSstReq = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        urlSstReq = os.path.join(self.paramGooddataUrl, 'gdc/account/login')
        sstReq = requests.post(urlSstReq, data=json.dumps(dataSstReq), headers=headerSstReq)
        scSstReq, jsSstReq = self._responseSplitter(sstReq)

        if scSstReq == 200:

            self.varTokenSst = jsSstReq['userLogin']['token']
            logging.info("Authentication successful. SST token obtained.")

        else:

            logging.error("Could not log in to GoodData. Response received: %s - %s." % (scSstReq, jsSstReq))
            sys.exit(1)
