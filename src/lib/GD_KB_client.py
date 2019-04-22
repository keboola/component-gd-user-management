import json
import requests
import logging
import sys
import secrets


class clientGoodDataKeboola:

    def __init__(self, username, password, pid, domain, gd_url, kbc_url, sapi_token):

        self.username = username
        self.password = password
        self.pid = pid
        self.sapi_token = sapi_token
        self.kbc_url = kbc_url
        self._KBC_header = {'X-StorageApi-Token': self.sapi_token}

        if domain.strip() != '':
            self.gd_url = domain.strip()
        else:
            self.gd_url = gd_url

        logging.info("GD domain set to %s." % self.gd_url)
        logging.info("KBC domain set to %s." % self.kbc_url)

        self._GD_get_SST_token()

    def _GD_get_SST_token(self):

        _data = f'''{{
            "postUserLogin":{{
                "login":"{self.username}",
                "password":"{self.password}",
                "remember": 1,
                "verify_level": 2
            }}
        }}
        '''

        headers = {"Content-Type": "application/json",
                   "Accept": "application/json"}

        url = self.gd_url + '/gdc/account/login'

        auth_response = requests.post(url, headers=headers, data=_data)
        auth_sc, auth_json = self.rsp_splitter(auth_response)

        if auth_sc in (200, 201, 202):

            # SST token is needed for further authorization, mainly
            # obtaining the TT token
            try:
                self.SST_token = auth_json['userLogin']['token']
                logging.info(
                    "Login to GoodData was successfull. SST token obtained.")
                # logging.debug("SST Token: %s" % self.SST_token)

            except KeyError:
                logging.error(
                    "Could not obtain the SST token. Please contact support.")
                sys.exit(1)
        else:

            logging.error(
                "Could not log in to GoodData, status code received was: %s." % str(auth_sc))
            logging.error("Response received: %s" % json.dumps(auth_json))
            sys.exit(1)

    def _GD_get_TT_token(self):

        # if not self.SST_token:
        #    self._GD_get_SST_token()

        headers = {"Content-Type": "application/json",
                   "Accept": "application/json",
                   "X-GDC-AuthSST": self.SST_token}

        url = self.gd_url + '/gdc/account/token'

        TT_response = requests.get(url, headers=headers)
        TT_sc, TT_json = self.rsp_splitter(TT_response)

        if TT_sc in (200, 201, 202):

            try:
                self.TT_token = TT_json['userToken']['token']
                # logging.info("Successfully obtained the TT token.")
                # logging.debug("TT Token: %s" % self.TT_token)

            except KeyError:
                logging.error("Log in successful, however TT token " +
                              "could not be obtained. Please contact support.")
                sys.exit(1)
        else:

            logging.error(
                "Could not log in to GoodData using SST, status code received was: %s." % str(TT_sc))
            logging.error("Response received: %s" % json.dumps(TT_json))
            sys.exit(1)

    def _GD_build_header(self):

        self._GD_get_TT_token()

        _header = {"Content-Type": "application/json",
                   "Accept": "application/json",
                   "X-GDC-AuthTT": self.TT_token}

        self._GD_header = _header

        # logging.debug("Request header: %s" % _header)

    def _GD_get_users(self):

        self._GD_build_header()

        url = self.gd_url + f'/gdc/projects/{self.pid}/users'

        users_request = requests.get(url, headers=self._GD_header)
        ur_sc = users_request.status_code
        ur_json = users_request.json()

        if ur_sc in (200, 201, 202):
            logging.info("Users were extracted successfully.")
            return ur_json
        else:
            logging.error("There was an issue extracting users from GD. " +
                          "Code received is %s." % str(ur_sc))
            logging.error("Response: %s" % json.dumps(ur_json))
            sys.exit(1)

    def _GD_get_attributes(self):

        self._GD_build_header()

        url = self.gd_url + f'/gdc/md/{self.pid}/query/attributes'

        attr_response = requests.get(url, headers=self._GD_header)

        att_sc = attr_response.status_code
        att_json = attr_response.json()

        if att_sc == 200:

            logging.info("Attributes were fetched successfully.")
            return att_json

        else:

            logging.info(
                "Could not fetch attributes. Response received status code %s." % att_sc)
            logging.debug('Response: %s' % json.dumps(att_json))
            sys.exit(1)

    def rsp_splitter(self, rsp):

        try:
            _rtrn_json = rsp.json()
        except ValueError:
            _rtrn_json = {}

        return rsp.status_code, _rtrn_json

    def _GD_get_attribute_values(self, attribute_uri):

        self._GD_build_header()

        url = self.gd_url + attribute_uri

        attr_response = requests.get(url, headers=self._GD_header)
        att_sc = attr_response.status_code

        if att_sc != 200:

            logging.error(
                "Could not obtain attribute values for attribute %s." % attribute_uri)

            return False, "Could not obtain attribute values for attribute %s." % attribute_uri

        _elmts = attr_response.json(
        )['attribute']['content']['displayForms'][0]['links']['elements']

        _paging = _elmts + '?limit=10000'
        self._GD_build_header()

        hasMore = True
        _out_elements = []
        while hasMore:

            el_url = self.gd_url + _paging

            el_response = requests.get(el_url, headers=self._GD_header)
            el_sc, el_json = self.rsp_splitter(el_response)

            _out_elements += el_json['attributeElements']['elements']

            _offset_url = el_json['attributeElements']['paging']['next']

            if _offset_url:
                _paging = _offset_url
            else:
                hasMore = False

        return True, _out_elements

    def _KBC_get_projects(self):

        url = self.kbc_url + '/projects'

        prj_response = requests.get(url, headers=self._KBC_header)

        prj_sc, prj_json = self.rsp_splitter(prj_response)

        if prj_sc in (200, 201, 202):

            return prj_json

        else:

            logging.error(
                "Could not obtain projects.")
            logging.error("Status code received %s." % prj_sc)
            logging.error("Response: %s" % json.dumps(prj_json))
            sys.exit(1)

    def _KBC_get_users(self):

        url = self.kbc_url + '/users'

        usr_response = requests.get(url, headers=self._KBC_header)

        usr_sc, usr_json = self.rsp_splitter(usr_response)

        if usr_sc in (200, 201, 202):

            return usr_json

        else:

            logging.error(
                "Could not obtain provisioned users for the project.")
            logging.error("Status code received %s." % usr_sc)
            logging.error("Response: %s" % json.dumps(usr_json))
            sys.exit(1)

    def _KBC_create_user(self, login, first_name, last_name):

        url = self.kbc_url + '/users'
        _pswd = secrets.token_hex(16)

        _data = f'''{{
            "login": "{login}",
            "password": "{_pswd}",
            "firstName": "{first_name}",
            "lastName": "{last_name}"
        }}
        '''

        logging.debug(_data)

        cu_response = requests.post(url, headers=self._KBC_header, data=_data)

        return self.rsp_splitter(cu_response)

    def _KBC_remove_user_from_project(self, login):

        url = self.kbc_url + f'/projects/{self.pid}/users/{login}'

        du_response = requests.delete(url, headers=self._KBC_header)

        return self.rsp_splitter(du_response)

    def _KBC_add_user_to_project(self, login, role):

        url = self.kbc_url + f'/projects/{self.pid}/users/{login}'

        _data = f'''{{
            "role": "{role}"
        }}
        '''

        au_response = requests.post(url, headers=self._KBC_header, data=_data)

        return self.rsp_splitter(au_response)

    def _GD_get_role_details(self, role_uri):

        url = self.gd_url + role_uri
        self._GD_build_header()

        role_detail_request = requests.get(url, headers=self._GD_header)
        return self.rsp_splitter(role_detail_request)

    def _GD_get_roles(self):

        url = self.gd_url + f'/gdc/projects/{self.pid}/roles'

        self._GD_build_header()

        roles_response = requests.get(url, headers=self._GD_header)
        roles_sc, roles_json = self.rsp_splitter(roles_response)

        if roles_sc != 200:

            logging.error(
                "Could not fetch project roles. Received code %s" % roles_sc)
            logging.error("Response: %s" % json.dumps(roles_json))
            sys.exit(1)

        _roles = roles_json['projectRoles']['roles']

        _GD_roles = {}

        for r in _roles:

            _, _details = self._GD_get_role_details(r)

            # logging.debug(_details)

            _role_title = _details['projectRole']['meta']['identifier']
            _GD_roles[_role_title] = r

        return _GD_roles

    def _GD_add_user_to_project(self, user_uri, role_uri):

        url = self.gd_url + f'/gdc/projects/{self.pid}/users'

        self._GD_build_header()

        _data = f'''{{
            "user": {{
                "content": {{
                    "status": "ENABLED",
                    "userRoles": [
                        "{role_uri}"
                    ]
                }},
                "links": {{
                    "self": "{user_uri}"
                }}
            }}
        }}
        '''

        au_response = requests.post(url, headers=self._GD_header, data=_data)

        return self.rsp_splitter(au_response)

    def _GD_remove_user_from_project(self, user_uri):

        url = self.gd_url + f'/gdc/projects/{self.pid}/users'

        self._GD_build_header()

        _data = f'''{{
            "user": {{
                "content": {{
                    "status": "DISABLED"
                }},
                "links": {{
                    "self": "{user_uri}"
                }}
            }}
        }}
        '''

        ru_response = requests.post(url, headers=self._GD_header, data=_data)

        return self.rsp_splitter(ru_response)

    def _GD_invite_users_to_project(self, invitation_dict):

        url = self.gd_url + f'/gdc/projects/{self.pid}/invitations'

        self._GD_build_header()

        _email = invitation_dict['_email']
        _role = invitation_dict['_role']
        _usrFilter = invitation_dict['_usrFilter']
        _usrFilter_str = self.list_to_str(_usrFilter)

        _data = f'''{{
            "invitations": [
              {{
                "invitation": {{
                  "content": {{
                    "email": "{_email}",
                    "userFilters": {_usrFilter_str},
                    "role": "{_role}",
                    "firstname": "",
                    "lastname": "",
                    "action": {{}}
                  }}
                }}
                }}
              ]
            }}
        '''

        logging.debug(_data)

        inv_response = requests.post(
            url, headers=self._GD_header, data=_data)

        return self.rsp_splitter(inv_response)

    @staticmethod
    def list_to_str(list):

        return '[' + ','.join('"{0}"'.format(x) for x in list) + ']'

    def _GD_create_MUF(self, expression, name):

        url = self.gd_url + f'/gdc/md/{self.pid}/obj'

        self._GD_build_header()

        _data = f'''{{
            "userFilter": {{
              "content": {{
                "expression": "{expression}"
              }},
              "meta": {{
                "category": "userFilter",
                "title": "{name}"
              }}
            }}
          }}
        '''

        logging.debug(_data)

        dp_rsp = requests.post(url, headers=self._GD_header, data=_data)

        return self.rsp_splitter(dp_rsp)

    def _GD_assign_MUF(self, user, userFilters):

        url = self.gd_url + f'/gdc/md/{self.pid}/userfilters'

        self._GD_build_header()

        userFilters_str = self.list_to_str(userFilters)

        _data = f'''{{
            "userFilters": {{
                "items": [
                    {{
                        "user": "{user}",
                        "userFilters": {userFilters_str}
                    }}
                ]
            }}
        }}
        '''

        logging.debug(_data)

        af_rsp = requests.post(url, headers=self._GD_header, data=_data)

        return self.rsp_splitter(af_rsp)

    def _GD_get_data_permissions_for_user(self, user_uri):

        url = self.gd_url + f'/gdc/md/{self.pid}/userfilters'

        self._GD_build_header()

        _params = {"users": f'{user_uri}'}

        logging.debug(_params)

        uf_rsp = requests.get(url, headers=self._GD_header, params=_params)

        return self.rsp_splitter(uf_rsp)
