# Imports
import bin.config
from abc import ABC, abstractmethod
import logging

# Attributes
config = bin.config.Config()
log = logging.getLogger(config.NAME)

# Base Class
class BaseAlert(ABC):
    def __init__(self, alert):
        self._alert = alert

    @abstractmethod
    def test(self):
        pass

    @abstractmethod
    def success(self, job):
        pass

    @abstractmethod
    def failure(self, job):
        pass
