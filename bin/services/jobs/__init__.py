# Imports
import bin.config
from celery import Task, current_app
from abc import ABC, abstractmethod
import datetime
import logging
import shutil
import os

# Attributes
config = bin.config.Config()
log = logging.getLogger(config.NAME)

# Base Class
class BaseJob(ABC, Task):
    def __init__(self, job):
        self._job = job

        self._temp_folder = f'/tmp/{self._job.name}'

    def _create_temp_folder(self):
        try:
            if not os.path.exists(self._temp_folder):
                log.debug(f'[{self._job.name}] Temp folder {self._temp_folder} did not exist so creating new one...')
                os.makedirs(self._temp_folder)
        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to create temp folder: {self._temp_folder}! Reason: {str(ex)}')

    def _generate_backup_ts(self):
        return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    @abstractmethod
    def _upload(self, backup_ts):
        pass

    def _cleanup_temp_folder(self):
        try:
            shutil.rmtree(self._temp_folder)
        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to remove temp folder: {self._temp_folder}! Reason: {str(ex)}')

    @abstractmethod
    def _cleanup(self):
        pass

    # Prevent more than one task running at the same time, prevents conflicts
    def is_running(self):
        i = current_app.control.inspect()
        servers = i.active()
        if servers:
            for tasks in servers.values():
                for task in tasks:
                    if task['name'] == self.name:
                        return True
        return False

    def status(self):
        return {} # TODO

    # Cancel task(s)
    def cancel(self):
        task_ids = []

        i = current_app.control.inspect()
        servers = i.active()
        if servers:
            for tasks in servers.values():
                for task in tasks:
                    if task['name'] == self.name:
                        task_ids.append(task.id)
        
        if len(task_ids) > 0:
            current_app.control.revoke(task_ids, terminate=True)

    @abstractmethod
    def run(self):
        pass
