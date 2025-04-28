# Imports
from bin.services.destinations import log, config, BaseDestination
import bin.error
import celery.exceptions
import datetime
import shutil
import os

# Class
class LocalDestination(BaseDestination):
    def __init__(self, destination):
        super().__init__(destination)

        self.name = f'local-{self._destination.name}'
        self._log_destination_type = f'{self._destination.name} local destination'

        self._remote_path = config.DESTINATION_LOCAL_PATH

    def check(self):
        # Test - not much of anything to test here...
        return True

    def upload(self, data):
        try:
            # Get data
            local_file = data['local_file']
            head, tail = os.path.split(local_file)
            remote_file = os.path.join(self._remote_path, tail)

            # Upload
            log.info(f'Copying {local_file} to {self._remote_path} for {self._log_destination_type}...')
            if not os.path.exists(self._remote_path):
                os.mkdir(self._remote_path)
                log.debug(f'Created missing {self._remote_path} directory in {self._log_destination_type}!')
            shutil.copyfile(local_file, remote_file)
        
        except Exception as ex:
            raise bin.error.UploadError(f'Unable to upload to {self._log_destination_type}! Reason: {str(ex)}')

    def run(self):
        self.update_state(state='RUNNING', meta={})

        try:
            # Get data
            oldest_timestamp = self._get_oldest_timestamp(self._destination.retention)

            # Cleanup
            log.info(f'Cleaning up old backups older than {oldest_timestamp} in {self._log_destination_type}...')
            backups_removed = 0
            for file in os.listdir(self._remote_path):
                if os.path.isfile(os.path.join(self._remote_path, file)):
                    file_datetime = datetime.datetime.strptime(file.split('.zip')[0], '%Y-%m-%d_%H-%M-%S')
                    if oldest_timestamp > file_datetime:
                        os.remove(os.path.join(self._remote_path, file))
                        backups_removed += 1
                        log.debug(f'Removed {os.path.join(self._remote_path, file)} from {self._log_destination_type} as it passed the retention policy!')
            
            log.info(f'Removed {backups_removed} old backups from {self._log_destination_type}!')
            self.update_state(state='SUCCESS', meta={})
        
        except Exception as ex:
            log.error(f'Unable to cleanup old backups in {self._log_destination_type}! Reason: {str(ex)}')
            self.update_state(state='ERROR', meta={})

        raise celery.exceptions.Ignore()
