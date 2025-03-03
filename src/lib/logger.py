import csv
import json
import logging
import os
import datetime


class Logger:

    """
    A class used for logging all necessary steps in the MUF process and their status.
    """

    def __init__(self, data_path, run_id=None, write_always: bool = False):

        """
        An initialization function.

        Parameters
        ----------
        data_path : str
            A data path, where the status file will be used.
        """

        self.data_path = data_path
        self.output_path = os.path.join(data_path, 'out', 'tables', 'status.csv')
        self.fields = ['user',
                       'action',
                       'status',
                       'timestamp',
                       'role',
                       'details',
                       'muf',
                       'run_id']
        self.run_id = run_id
        self.write_always = write_always
        if self.write_always:
            logging.info("Parameter fail_on_error is set to true, the component will end with error if it encounters "
                         "any problems during run.")

        logging.info("Status file saved to %s." % self.output_path)

        with open(self.output_path, 'w') as log_file:

            writer = csv.DictWriter(log_file,
                                    self.fields,
                                    restval='',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_ALL)

            writer.writeheader()

        self.create_manifest()

    def make_log(self, user, action, success, role, details, muf):

        """
        A function, that writes a row to a status file.

        Parameters
        ----------
        self : class
        user : str
            A user, for which the action was performed.
        action : str
            Name of the action performed.
        success : bool
            Boolean value whether the action was successful.
        role : str
            Role of the user.
        details : str
            Any additional details about the action.
        muf : str
            A muf expression used for the user.
        """

        _ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f UTC')
        if success:
            success_str = "SUCCESS"
        else:
            success_str = "ERROR"

        _to_write = {'user': user,
                     'action': action,
                     'status': success_str,
                     'timestamp': _ts,
                     'role': role,
                     'details': details,
                     'muf': muf,
                     'run_id': self.run_id}

        with open(self.output_path, 'a') as log_file:

            writer = csv.DictWriter(log_file,
                                    self.fields,
                                    restval='',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_ALL)

            writer.writerow(_to_write)

    def create_manifest(self):

        """
        A function creating manifest for the status file.

        Parameters
        ----------
        self : class
        """

        _out_path = self.output_path
        _manifest_path = _out_path + '.manifest'

        _man = {"destination": "out.c-GDUserManagement.status",
                "incremental": True,
                "delimiter": ","}

        if self.write_always:
            _man["write_always"] = True

        with open(_manifest_path, 'w') as f:

            json.dump(_man, f)
