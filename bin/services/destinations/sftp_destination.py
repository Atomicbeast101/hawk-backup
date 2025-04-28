# Imports
from bin.services.destinations import log, BaseDestination
import bin.extract
import bin.error
import celery.exceptions
import traceback
import datetime
import pysftp
import os

# Class
class SFTPDestination(BaseDestination):
    def __init__(self, destination):
        super().__init__(destination)

        self.name = f'sftp-{self._destination.name}'
        self._log_destination_type = f'{self._destination.name} SFTP destination'

        self._server = self._destination.config['server']
        self._port = self._destination.config['port']
        self._username = self._destination.config['username']
        self._password = bin.extract.get_destination_secrets_from_env(destination.name)['password'] if 'password' not in self._destination.config else self._destination.config['password']
        self._sftp_options = pysftp.CnOpts()
        self._sftp_options.hostkeys = None
        self._remote_path = self._destination.config['path']

    def check(self):
        # Test
        try:
            with pysftp.Connection(self._server, port=self._port, username=self._username, password=self._password, cnopts=self._sftp_options):
                log.debug(f'Successfully tested connection to {self._log_destination_type}!')
            
            return True

        except Exception as ex:
            log.warning(f'Unable to make a test connection to {self._log_destination_type}! Reason: {str(ex)}')
            log.debug(traceback.format_exc())
            
        return False

    def upload(self, data):
        try:
            # Get data
            local_file = data['local_file']
            head, tail = os.path.split(local_file)
            remote_file = os.path.join(self._remote_path, tail)

            # Upload
            log.info(f'Uploading {local_file} to {self._remote_path} for {self._log_destination_type}...')
            with pysftp.Connection(self._server, port=self._port, username=self._username, password=self._password, cnopts=self._sftp_options) as sftp:
                if not sftp.exists(self._remote_path):
                    sftp.mkdir(self._remote_path)
                    log.debug(f'Created missing {self._remote_path} directory in {self._log_destination_type}!')
                sftp.put(local_file, remote_file)

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
            with pysftp.Connection(self._server, port=self._port, username=self._username, password=self._password, cnopts=self._sftp_options) as sftp:
                for file in sftp.listdir_attr(self._remote_path):
                    file_datetime = datetime.datetime.strptime(file.filename.split('.zip')[0], '%Y-%m-%d_%H-%M-%S')
                    if oldest_timestamp > file_datetime:
                        sftp.remove(f'{self._remote_path}/{file.filename}')
                        backups_removed += 1
                        log.debug(f'Removed {os.path.join(self._remote_path, file)} from {self._log_destination_type} as it passed the retention policy!')
            
            log.info(f'Removed {backups_removed} old backups from {self._log_destination_type}!')
            self.update_state(state='SUCCESS', meta={})

        except Exception as ex:
            log.error(f'Unable to cleanup old backups in {self._log_destination_type}! Reason: {str(ex)}')
            self.update_state(state='ERROR', meta={})

        raise celery.exceptions.Ignore()
