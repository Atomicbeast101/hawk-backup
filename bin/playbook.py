# Imports
import ansible_runner
import traceback
import datetime

# Classes
class BorgPlaybook:
    def __init__(self, log, global_func, name, config, job_config, alerts):
        super().__init__(log, global_func, name, config)

        self._type = 'BorgBackup'
        self._config = config

    # Create directory in SFTP endpoint if that's the destination selected

class CustomPlaybook:
    def __init__(self, log, global_func, name, config, job_config, alerts):
        super().__init__(log, global_func, name, config)

        self._type = 'Ansible'
        self._config = config
        
