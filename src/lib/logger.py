import csv
import os
import datetime


class componentLogger:

    def __init__(self, data_path):

        self.data_path = data_path
        self.output_path = os.path.join(data_path, 'out', 'tables', 'status.csv')
        self.fields = ['user',
                       'action',
                       'status',
                       'timestamp',
                       'role',
                       'details',
                       'muf']

        with open(self.output_path, 'w') as log_file:

            writer = csv.DictWriter(log_file,
                                    self.fields,
                                    restval='',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_ALL)

            writer.writeheader()

    def make_log(self, user, action, success, role, details, muf):

        _ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
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
                     'muf': muf}

        with open(self.output_path, 'a') as log_file:

            writer = csv.DictWriter(log_file,
                                    self.fields,
                                    restval='',
                                    extrasaction='ignore',
                                    quotechar='"',
                                    quoting=csv.QUOTE_ALL)

            writer.writerow(_to_write)
