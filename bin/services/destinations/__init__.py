# Imports
import bin.config
from celery import Task, current_app
from abc import ABC, abstractmethod
import datetime
import logging

# Attributes
config = bin.config.Config()
log = logging.getLogger(config.NAME)

# Base Class
class BaseDestination(ABC, Task):
    def __init__(self, destination):
        self._destination = destination

        self.name = 'local-TEMPLATE'

    def _get_oldest_timestamp(retention):
        if retention.endswith('d'):
            days = int(retention[:-1])
            return datetime.datetime.now() - datetime.timedelta(days=days)

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def upload(self, data):
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
