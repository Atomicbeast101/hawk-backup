# Imports
import bin.cleanup
import bin.upload
from abc import ABC, abstractmethod
import datetime
import shutil
import os
import re

# Class
class Service(ABC):
    def __init__(self, log, global_func, name, config):
        self._log = log
        self._global_func = global_func
        self._name = name
        self._config = config
        self._temp_folder = f'/tmp/hawkbackup/{self._name}'

        self._uploader = bin.upload.Upload(log, global_func)
        self._cleanuper = bin.cleanup.CleanUp(log, global_func)

    def _get_destination(self, dest_id):
        for destination in self._config['destinations']:
            if destination['name'] == dest_id:
                return destination

    def _convert_retention(self, raw_retention):
        retention = {
            'level': None,
            'number': -1
        }

        # Days
        if re.match(r'^[0-9]+d$', raw_retention):
            retention['level'] = 'days'
            retention['number'] = int(raw_retention[:-1])

        return retention

    def _create_temp_folder(self):
        try:
            if not os.path.exists(self._temp_folder):
                self._log.debug(f'Temp folder {self._temp_folder} did not exist so creating new one... [{self._name}]')
                os.makedirs(self._temp_folder)
        except Exception as ex:
            raise Exception(f'Unable to create temp folder: {self._temp_folder} [{self._name}]! Reason: {str(ex)}')

    def _generate_backup_ts(self):
        return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    @abstractmethod
    def _upload(self, backup_ts):
        pass

    def _cleanup_temp_folder(self):
        try:
            shutil.rmtree(self._temp_folder)
        except Exception as ex:
            raise Exception(f'Unable to remove temp folder: {self._temp_folder} [{self._name}]! Reason: {str(ex)}')

    @abstractmethod
    def _cleanup(self):
        pass

    @abstractmethod
    def backup(self):
        pass
