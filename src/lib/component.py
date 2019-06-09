import csv
import json
import logging
import os
import sys
from lib.GD_KB_client import clientGoodDataKeboola
from lib.logger import Logger
from lib.user import User
from kbc.env_handler import KBCEnvHandler


class Component(KBCEnvHandler):

    """
    The main component class, a children class of KBCEnvHandler.

    See keboola-python-util-lib package: https://bitbucket.org/kds_consulting_team/keboola-python-util-lib/src/master/
    """

    def __init__(self, username_key, password_key, pid_key,
                 domain_key, gd_url_key, kbc_prov_key, MANDATORY_PARS):
        """
        Init function.
        In addition to initialization of the class, the function checks whether provided PID is in the list
        of PIDs provisioned by the Keboola GD Writer, obtains attributes of the whole GD project, extracts users
        from both Keboola and GD environments, maps Keboola roles to GD roles, checks admin privileges and ensures
        the admin user has no data permissions assigned to themselves.

        Parameters
        ----------
        username_key : str
            A key in dictionary for username parameter.
        password_key : str
            A key in dictionary for password parameter.
        pid_key : str
            A key in dictionary for PID parameter.
        domain_key : str
            A key in dictionary for domain parameter.
        gd_url_key : str
            A key in dictionary for GD URL stack parameter.
        kbc_prov_key : str
            A key in dictionary for Keboola Provisioning API stack parameter.
        MANDATORY_PARAMS : list
            A list of mandatory parameters.
        """

        KBCEnvHandler.__init__(self, MANDATORY_PARS)

        sapi_token = self.get_storage_token()
        username = self.cfg_params[username_key]
        password = self.cfg_params[password_key]
        pid = self.cfg_params[pid_key]
        domain = self.cfg_params[domain_key]
        gd_url = self.image_params[gd_url_key]
        kbc_prov_url = self.image_params[kbc_prov_key]

        self.client = clientGoodDataKeboola(username, password, pid, domain,
                                            gd_url, kbc_prov_url, sapi_token)

        self.input_files = self.configuration.get_input_tables()
        self.log = Logger(self.data_path)
        self._compare_projects()
        self._get_all_attributes()
        self._get_all_users()
        self._map_roles()
        self._GD_check_user_admin()
        self._GD_check_admin_permissions()

    def _compare_projects(self):
        """
        A function, that compares provided PID with those provisioned by GD Writer.

        Parameters
        ----------
        self : class

        Raises
        ------
        SystemExit
            If the provided PID is not in the list of projects provosioned by Keboola.
        """

        _projects = self.client._KBC_get_projects()
        _projects_ids = [p['pid'] for p in _projects]

        if self.client.pid not in _projects_ids:

            logging.error(
                "GoodData Project ID %s is not located in this project." % self.client.pid)
            logging.error(
                "You can't provision users from a different project than the origin project.")
            sys.exit(1)

    def _get_all_attributes(self):
        """
        A function for obtaining all attributes from the GD project.

        Parameters
        ----------
        self : class
        """

        logging.info("Obtaining all attributes for the project.")
        _att_out = {}

        _attributes = self.client._GD_get_attributes()['query']['entries']

        for a in _attributes:

            _identifier = a['identifier']
            _link = a['link']

            _att_out[_identifier] = {'identifier': _identifier,
                                     'uri': _link}

        self.attributes = _att_out
        self.log.make_log('admin', 'GET_ATTRIBUTES', True, '', '', '')

    def _get_all_users(self):
        """
        A function to obtain all users provisioned by Keboola and within GD project.

        Parameters
        ----------
        self : class
        """

        _GD_users = self.client._GD_get_users()['users']
        _GD_users_out = {}

        for u in _GD_users:

            logging.debug(u)

            _email = u['user']['content']['email']
            _user_uri = u['user']['links']['self']
            _role = u['user']['content']['userRoles']

            if _role != []:

                _role_uri = _role[0]

            else:

                _role_uri = ''

            _status = u['user']['content']['status']

            _GD_users_out[_email] = {'email': _email,
                                     'uri': _user_uri,
                                     'role': _role_uri,
                                     'status': _status}

        self.log.make_log('admin', 'GET_GD_USERS', True, '', '', '')
        self.users_GD = _GD_users_out

        _KB_users = self.client._KBC_get_users()

        logging.debug("Keboola users:")
        logging.debug(_KB_users)

        _KB_users_out = {}

        for u in _KB_users:

            _email = u['login']
            _user_uri = '/gdc/account/profile/' + u['uid']

            _KB_users_out[_email] = {'email': _email,
                                     'uri': _user_uri}

        self.log.make_log('admin', 'GET_KBC_USERS', True, '', '', '')
        self.users_KB = _KB_users_out

    def _map_roles(self):
        """
        A function mapping GD roles to KBC ones.

        Parameters
        ----------
        self : class

        Returns
        -------

        Raises
        ------
        """

        logging.info("Mapping GD roles to KBC equivalents.")
        _GD_roles = self.client._GD_get_roles()

        _KB_roles = ['admin',
                     'dashboardOnly',
                     'editor',
                     'editorInvite',
                     'editorUserAdmin',
                     'explorer',
                     'explorerOnly',
                     'keboolaEditorPlus',
                     'readOnlyUser',
                     'readOnlyNoExport']

        _role_map = {'admin': 'adminRole',
                     'dashboardOnly': 'dashboardOnlyRole',
                     'editor': 'editorRole',
                     'editorInvite': 'editorInviteRole',
                     'editorUserAdmin': 'editorUserAdminRole',
                     'explorer': 'explorerRole',
                     'explorerOnly': 'explorerOnlyRole',
                     'keboolaEditorPlus': 'keboolaEditorPlusRole',
                     'readOnlyUser': 'readOnlyUserRole',
                     'readOnlyNoExport': 'readOnlyNoExportRole'}

        _role_matrix = {}

        for r in _KB_roles:

            _gd_map = _role_map.get(r)
            _gd_uri = _GD_roles.get(_gd_map)

            _role_matrix[r] = {'KBC': r,
                               'GD': _gd_map,
                               'GD_URI': _gd_uri}

        self._roles_map = _role_matrix
        self.log.make_log('admin', 'MAP_ROLES', True, '',
                          json.dumps(_role_matrix), '')

    def _GD_check_admin_permissions(self):
        """
        A function checking, whether admin user has any data permissions assigned to them.

        Parameters
        ----------
        self : class

        Raises
        ------
        SystemExit
            If the admin user has admin permissions assigned.
        """

        _login = self.client.username
        _login_uri = self.users_GD[_login]['uri']

        _sc, _js = self.client._GD_get_data_permissions_for_user(_login_uri)

        _usr_filters = _js["userFilters"]["items"]

        if len(_usr_filters) != 0:

            logging.error("Admin account cannot have any data permissions assigned to them. Please, use" +
                          " a different user or remove data permissions.")

            sys.exit(1)

    def _GD_check_user_admin(self):
        """
        A function checking whether provided user is admin within GD project.

        Parameters
        ----------
        self : class

        Raises
        ------
        SystemExit
            If provided user is not admin.
        """

        _login = self.client.username

        _usr_information = self.users_GD.get(_login)
        logging.debug(_usr_information)

        if _usr_information:

            _usr_role_uri = _usr_information['role']
            _usr_role_name = None

            for r in self._roles_map:

                _role_dict = self._roles_map[r]

                if _role_dict['GD_URI'] == _usr_role_uri:

                    _usr_role_name = r
                    break

            if _usr_role_name == 'admin':

                logging.info("Verified admin privileges for user %s." % _login)

            else:

                logging.error(
                    "User %s does not have admin privileges." % _login)
                sys.exit(1)

        else:

            logging.error("User %s is not in the project." % _login)
            sys.exit(1)

    def create_muf_expression(self, muf_str):
        """
        A function for creating MUF expressions, i.e. attributes' and values' names are replaced by their URIs.

        Parameters
        ----------
        self : class
        muf_str : str
            A string containing MUF expression.

        Returns
        -------
        tuple
            A tuple of length 2. The first element marks, whether the operation was successful. If the first element
            is true, the second element is a list of user filters expressions. If the first element is false, the
            second element is an error message.
        """

        try:

            _muf_json = json.loads(muf_str)

        except ValueError as e:

            return False, e

        _muf_expr = []

        for mf in _muf_json:

            try:
                _attr = mf['attribute']
                _val = mf['value']
                _oper = mf['operator']

            except KeyError as e:

                return False, "Key %s is missing in MUF json." % e

            logging.debug(_attr)
            logging.debug(_val)
            logging.debug(_oper)

            if not isinstance(_val, list):

                return False, "Attribute values must be a list."

            elif len(_val) > 1 and _oper not in ('IN', 'NOT IN'):

                return False, "Unique value must be provided for non-IN operators."

            # Possible improvement for AND operator in the future.
            if isinstance(_attr, str):

                _attr_GD = self.attributes.get(_attr)

                if not _attr_GD:

                    return False, "Attribute %s is not in the project." % _attr

                else:

                    _attr_uri = _attr_GD.get('uri')

                if not _attr_uri:

                    return False, "Attribute %s has no URI." % _attr

                _attr_vals = self.get_attribute_values(_attr_uri)

                if _attr_vals is False:

                    return False, "Could not obtain values for attribute %s" % _attr_uri

                _attr_vals_uri = []

                for v in _val:

                    _v_uri = _attr_vals.get(v)

                    if _v_uri:

                        _attr_vals_uri += [_v_uri]

                    else:

                        return False, "Attribute %s has no value %s." % (_attr, v)

                if _oper in ('IN', 'NOT IN'):

                    _attr_vals_uri = self._expr_list_to_tuple(_attr_vals_uri)

                else:

                    _attr_vals_uri = self._expr_list_to_str(_attr_vals_uri)

                _expr = ' '.join([self._expr_str_to_list(_attr_uri),
                                  _oper,
                                  _attr_vals_uri])

                _muf_expr += [_expr]

            else:

                return False, "Attribute lists are not yet supported."

        return True, _muf_expr

    def get_attribute_values(self, attribute_uri):
        """
        A function, getting and parsing the attributes.

        Parameters
        ----------
        _attribute_uri : str
            A URI of an attribute, for which values are to be obtained.

        Returns
        -------
        dict
            A dictionary, with values' title as a key and respective URI as a value.
        """

        _sc, _values = self.client._GD_get_attribute_values(attribute_uri)

        if _sc is False:

            return False

        _val_out = {}

        for v in _values:

            _title = v['title']
            _uri = v['uri']

            _val_out[_title] = _uri

        return _val_out

    @staticmethod
    def _expr_list_to_tuple(_list):
        """
        A method converting a list of value into a tuple, with elements surrounded by square brackets.

        Parameters
        ----------
        _list : list
            A list to be converted.

        Returns
        -------
        str
            A string-like-tuple.
        """

        return '(' + ','.join('[{0}]'.format(x) for x in _list) + ')'

    @staticmethod
    def _expr_str_to_list(_str):
        """
        A method converting string to a string like list.

        Parameters
        ----------
        _str : str
            A string to be converted.

        Returns
        -------
        str
            A converted string, encapsulated by square brackets.
        """

        return '[' + _str + ']'

    @staticmethod
    def _expr_list_to_str(_list):
        """
        A method converting a list-like expression to string-like-list.

        Parameters
        ----------
        _list : list
            List of values to be converted.

        Returns
        -------
        str
            A string, encapsulated by square brackets. All contents of a list are concatenated.
        """

        return '[' + ''.join(_list) + ']'

    def create_muf(self, muf_expr):
        """
        Creates data permission from a list.

        Parameters
        ----------
        muf_expr : list
            A list of expressions, for which data permissions should be created.

        Returns
        -------
        tuple
            A tuple with 2 elements. First element captures, whether the an attempt to create MUFs for
            all elements in the list was successful. If the first argument returns `SUCCESS`, a list
            with URIs to filter is returned, otherwise an error message is returned.
        """
        _muf_ids = []

        for mf in muf_expr:

            mf_sc, mf_json = self.client._GD_create_MUF(mf, 'muf')

            if mf_sc == 200:

                _muf_ids += [mf_json['uri']]

            else:

                return False, "Could not create MUF. Received: %s" % mf_json['error']['message']

        return True, _muf_ids

    def check_membership(self, user):
        """
        A function checking whether a user is in the Keboola organization or GD project.

        Parameters
        ----------
        self : class
        user : User class
            A class representing user.

        Raises
        ------
        SystemExit
            If none of the conditions is met.
        """

        _login = user.login
        _user_action = user.action

        if _user_action not in ("ENABLE", "DISABLE", "INVITE"):

            self.log.make_log(_login, _user_action, False,
                              user.role, "User action must be ENABLE or DISABLE.", '')
            user._app_action = 'SKIP'

            return

        _in_org = _login in self.users_KB
        _in_prj = _login in self.users_GD

        if _in_prj is True:

            _status = self.users_GD[_login]['status']
            user.uri = self.users_GD[_login]['uri']

            if _status == 'ENABLED' and _user_action == 'ENABLE':

                user._app_action = 'GD_DISABLE MUF GD_ENABLE'

            elif _status == 'ENABLED' and _user_action == 'DISABLE':

                user._app_action = 'GD_DISABLE'

            elif _status == 'DISABLED' and _user_action == 'ENABLE':

                user._app_action = 'GD_DISABLE MUF GD_ENABLE'

            elif _status == 'DISABLED' and _user_action == 'DISABLE':

                user._app_action = 'SKIP'

            elif _status == 'ENABLED' and _user_action == 'INVITE':

                user._app_action = 'GD_DISABLE MUF GD_ENABLE'

            elif _status == 'DISABLED' and _user_action == 'INVITE':

                user._app_action = 'MUF GD_INVITE'

            else:

                logging.error("Unknown error during URI check.")
                sys.exit(2)

        elif _in_prj is False and _in_org is True:

            user.uri = self.users_KB[_login]['uri']

            if _user_action == 'ENABLE':

                user._app_action = 'MUF KB_ENABLE'

            elif _user_action == 'DISABLE':

                user._app_action = 'SKIP'

            elif _user_action == 'INVITE':

                user._app_action = 'MUF GD_INVITE'

            else:

                logging.error("Unknown error during URI check.")
                sys.exit(2)

        elif _in_prj is False and _in_org is False:

            user.uri = None

            if user.action == 'DISABLE':

                user._app_action == 'SKIP'

            else:

                user._app_action = 'TRY_KB_CREATE MUF ENABLE_OR_INVITE'

        else:

            logging.error("Unknown error while checking for membership.")
            sys.exit(2)

    def create_muf_uri(self, user):
        """
        A function combining creating MUF expression function and creating MUFs.

        Parameters
        ----------
        self : class
        user : User class

        Returns
        -------
        tuple
            A tuple with 2 elements. First element captures, whether the an attempt to create MUFs for
            all elements in the list was successful. If the first argument returns `SUCCESS`, a list
            with URIs to filter is returned, otherwise an error message is returned.

        Raises
        ------
        """

        _muf_str = user.muf
        logging.debug(_muf_str)

        if _muf_str == '[]':

            return True, []

        _status, _muf_expr = self.create_muf_expression(_muf_str)

        self.log.make_log(user.login, "CREATE_MUF_EXPR", _status,
                          user.role, str(_muf_expr), user.muf)

        logging.debug("Creating: %s" % str(_status))
        logging.debug("MUF EXPR: %s" % _muf_expr)

        if _status is False:

            return False, []

        _status, _muf_uri = self.create_muf(_muf_expr)

        self.log.make_log(user.login, "CREATE_MUF", _status,
                          user.role, str(_muf_uri), user.muf)

        if _status is False:

            return False, []

        else:

            return True, _muf_uri

    def map_role_to_uri(self, user):
        """
        A function mapping user role to its URI.

        Parameters
        ----------
        self : class
        user : User class
        """

        _role = user.role
        user.role_uri = self._roles_map[_role]['GD_URI']

    def run(self):
        """
        The main run function

        Parameters
        ----------
        self : class
        """

        for f in self.input_files:

            _path = os.path.join(self.data_path, 'in',
                                 'tables', f['destination'])

            with open(_path) as file:

                _rdr = csv.DictReader(file)

                for row in _rdr:

                    try:

                        _login = row['login']
                        _action = row['action']
                        _role = row['role']
                        _muf = row['muf']
                        _fn = row['first_name']
                        _ln = row['last_name']

                        user = User(_login, _role, _muf, _action, _fn, _ln)

                    except KeyError as e:

                        logging.error(
                            "Column %s is missing from the .csv file." % e)
                        sys.exit(1)

                    logging.info("Starting process for user %s." % _login)

                    _av_roles = list(self._roles_map.keys())

                    if _role not in _av_roles:

                        self.log.make_log(user.login, "ROLE_ERROR", False,
                                          user.role, "Role must be one of %s" % str(_av_roles), user.muf)

                        logging.warn(
                            "There were some errors for user %s." % _login)
                        continue

                    self.check_membership(user)

                    logging.info("User %s was assigned the following action: %s" % (
                        user.login, user._app_action))

                    self.map_role_to_uri(user)

                    if user._app_action == 'SKIP':

                        self.log.make_log(user.login, "NO_ACTION", True,
                                          user.role, "No action needed.", user.muf)

                        logging.debug("Skipping user %s" % user.login)

                        continue

                    elif user._app_action == 'GD_DISABLE':

                        logging.debug(
                            "Attemmpting to disable user %s" % user.login)

                        _sc, _js = self.client._GD_remove_user_from_project(
                            user.uri)

                        if _sc == 200:

                            self.log.make_log(user.login, "DISABLE_IN_PRJ", True,
                                              user.role, '', user.muf)

                        else:

                            self.log.make_log(user.login, "DISABLE_IN_PRJ", False,
                                              user.role, _js, user.muf)

                    elif user._app_action == 'GD_DISABLE MUF GD_ENABLE':

                        logging.debug(
                            "User %s will be disabled, assigned MUFs and re-enabled." % user.login)
                        logging.debug("Disabling...")

                        _sc, _js = self.client._GD_remove_user_from_project(
                            user.uri)

                        if _sc == 200:

                            self.log.make_log(user.login, "DISABLE_IN_PRJ", True,
                                              user.role, '', user.muf)

                        else:

                            self.log.make_log(user.login, "DISABLE_IN_PRJ", False,
                                              user.role, _js, user.muf)

                            logging.warn(
                                "There were some errors for user %s." % _login)
                            continue

                        logging.debug("Creating MUFs...")
                        _status, _muf = self.create_muf_uri(user)

                        logging.debug(_muf)

                        if _status is False:

                            logging.warn(
                                "There were some errors for user %s when creating URIs for MUFs." % _login)
                            continue

                        logging.debug("Assigning MUFs...")
                        _sc, _js = self.client._GD_assign_MUF(user.uri, _muf)

                        if _sc == 200:

                            self.log.make_log(user.login, "ASSIGN_MUF", True,
                                              user.role, '', user.muf)

                        else:

                            self.log.make_log(user.login, "ASSIGN_MUF", False,
                                              user.role, _js, user.muf)

                            logging.debug(_js)

                            logging.warn(
                                "There were some errors for user %s when assigning MUFs." % _login)
                            continue

                        logging.debug("Re-enabling user...")
                        _sc, _js = self.client._GD_add_user_to_project(
                            user.uri, user.role_uri)

                        _failed = _js['projectUsersUpdateResult']['failed']

                        if len(_failed) == 0 and _sc == 200:

                            self.log.make_log(user.login, "ENABLE_IN_PRJ", True,
                                              user.role, '', user.muf)

                        else:

                            self.log.make_log(user.login, "ENABLE_IN_PRJ", True,
                                              user.role, _failed[0]['message'], user.muf)
                            logging.warn(
                                "There were some errors for user %s." % _login)

                    elif user._app_action in ('MUF GD_INVITE', 'TRY_KB_CREATE MUF ENABLE_OR_INVITE'):

                        if user._app_action == 'TRY_KB_CREATE MUF ENABLE_OR_INVITE':

                            logging.info(
                                "Attempting to create user %s in organization." % user.login)

                            _sc, _js = self.client._KBC_create_user(
                                user.login, user.first_name, user.last_name)

                            if _sc == 201:

                                user.uri = '/gdc/account/profile/' + _js['uid']
                                self.log.make_log(
                                    user.login, "USER_CREATE", True, user.role, user.uri, user.muf)

                                logging.debug(
                                    "User created successfully. URI: %s" % user.uri)

                            elif _sc == 422:

                                self.log.make_log(
                                    user.login, "USER_CREATE", False, user.role, _js['errorMessage'], user.muf)

                                logging.warn(
                                    "There were some errors for user %s." % _login)
                                continue

                            else:

                                logging.warn(
                                    "User %s already exists in a different organization." % user.login)

                        logging.debug("Creating MUFs...")
                        _status, _muf = self.create_muf_uri(user)

                        if _status is False:

                            logging.warn(
                                "Could not create MUF for user %s." % _login)
                            continue

                        if user.uri is None or (user.uri is not None and user.action == 'INVITE'):

                            logging.debug("Inviting user...")

                            _dict = {'_email': user.login,
                                     '_role': user.role_uri,
                                     '_usrFilter': _muf}

                            _sc, _js = self.client._GD_invite_users_to_project(
                                _dict)

                            _d_mismatch = _js['createdInvitations']['loginsDomainMismatch']
                            _d_inproject = _js['createdInvitations']['loginsAlreadyInProject']

                            if len(_d_mismatch) == 0 and len(_d_inproject) == 0:

                                self.log.make_log(user.login, "INVITE_TO_PRJ", True,
                                                  user.role, '', user.muf)

                            else:

                                logging.warn(
                                    "There were some errors when inviting user %s." % _login)
                                self.log.make_log(user.login, "INVITE_TO_PRJ", False,
                                                  user.role, _js, user.muf)

                        else:

                            logging.debug("Assigning MUFs...")

                            _sc, _js = self.client._GD_assign_MUF(
                                user.uri, _muf)

                            if _sc == 200:

                                self.log.make_log(user.login, "ASSIGN_MUF", True,
                                                  user.role, '', user.muf)

                            else:

                                self.log.make_log(user.login, "ASSIGN_MUF", False,
                                                  user.role, _js, user.muf)

                                logging.debug(_js)

                                logging.warn(
                                    "There were some errors for user %s when assigning MUFs." % _login)
                                continue

                            logging.debug("Enabling user in the project...")
                            _sc, _js = self.client._KBC_add_user_to_project(
                                user.login, user.role)

                            if _sc == 204:

                                self.log.make_log(user.login, "ENABLE_IN_PRJ", True,
                                                  user.role, '', user.muf)

                            else:

                                self.log.make_log(user.login, "ENABLE_IN_PRJ", True,
                                                  user.role, _js, user.muf)

                    elif user._app_action == 'MUF KB_ENABLE':

                        logging.debug(
                            "User will be assigned MUFs and enabled.")
                        logging.debug("Creating MUFs...")

                        _status, _muf = self.create_muf_uri(user)

                        if _status is False:

                            logging.warn(
                                "Could not create MUF for user %s." % user.login)
                            continue

                        logging.debug("Assigning MUFs...")

                        _sc, _js = self.client._GD_assign_MUF(user.uri, _muf)

                        if _sc == 200:

                            self.log.make_log(user.login, "ASSIGN_MUF", True,
                                              user.role, '', user.muf)

                        else:

                            self.log.make_log(user.login, "ASSIGN_MUF", False,
                                              user.role, _js, user.muf)

                            logging.debug(_js)

                            logging.warn(
                                "There were some errors for user %s when assigning MUFs." % _login)
                            continue

                        logging.debug("Enabling user in the project...")
                        _sc, _js = self.client._KBC_add_user_to_project(
                            user.login, user.role)

                        if _sc == 204:

                            self.log.make_log(user.login, "ENABLE_IN_PRJ", True,
                                              user.role, '', user.muf)

                        else:

                            self.log.make_log(user.login, "ENABLE_IN_PRJ", False,
                                              user.role, _js, user.muf)

                    logging.info("Process for user %s has ended." % user.login)
