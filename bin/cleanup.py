# Imports
import datetime
import pysftp
import os

# Class
class CleanUp:
    def __init__(self, log, global_func):
        self._log = log
        self._global_func = global_func
    
        self._sftp_options = pysftp.CnOpts()
        self._sftp_options.hostkeys = None

    def _get_oldest_ts(self, retention_level, retention_number):
        if retention_level == 'days':
            return datetime.datetime.now() - datetime.timedelta(days=retention_number)

    def _cleanup_sftp(self, retention_level, retention_number, server, port, username, password, remote_path):
        try:
            oldest_ts = self._get_oldest_ts(retention_level, retention_number)

            self._log.debug(f'Cleaning up old files older than {oldest_ts} in {server},{port}:{remote_path} SFTP endpoint...')
            files_removed = 0
            with pysftp.Connection(server, port=port, username=username, password=password, cnopts=self._sftp_options) as sftp:
                for file in sftp.listdir_attr(remote_path):
                    file_datetime = datetime.datetime.strptime(file.filename.split('.zip')[0], '%Y-%m-%d_%H-%M-%S')
                    if oldest_ts > file_datetime:
                        sftp.remove(f'{remote_path}/{file.filename}')
                        files_removed += 1
                        self._log.debug(f'Removed {sftp.pwd}/{file.filename} from {server},{port}:{remote_path} SFTP endpoint as it passed the retention policy.')   
            self._log.info(f'Cleaned up {files_removed} from {server},{port}:{remote_path} SFTP endpoint!')
        except Exception as ex:
            raise Exception(f'Error when trying to cleanup the SFTP endpoint: {str(ex)}')

    def run(self, name, retention, destination):
        if 'sftp' in destination:
            self._cleanup_sftp(
                retention_level=retention['level'],
                retention_number=retention['number'],
                server=destination['sftp']['server'],
                port=destination['sftp']['port'],
                username=str(destination['sftp']['username']),
                password=self._global_func.get_destination_password(destination['sftp'], 'jobs', name),
                remote_path=os.path.join(destination['sftp']['path'], name)
            )
