# Imports
import pysftp
import os

# Class
class Upload:
    def __init__(self, log, global_func):
        self._log = log
        self._global_func = global_func
    
        self._sftp_options = pysftp.CnOpts()
        self._sftp_options.hostkeys = None

    def _push_to_sftp(self, local_file, server, port, username, password, remote_path):
        try:
            head, tail = os.path.split(local_file)
            remote_file = os.path.join(remote_path, tail)
            
            self._log.debug(f'Uploading {local_file} to {server},{port}:{remote_file} SFTP endpoint...')
            with pysftp.Connection(server, port=port, username=username, password=password, cnopts=self._sftp_options) as sftp:
                if not sftp.exists(remote_path):
                    sftp.mkdir(remote_path)
                    self._log.debug(f'Created {remote_path} directory as it did not exist in SFTP endpoint!')
                sftp.put(local_file, remote_file)
        except Exception as ex:
            raise Exception(f'Error when trying to upload to SFTP endpoint: {str(ex)}')

    def run(self, name, local_file, destination):
        if 'sftp' in destination:
            self._push_to_sftp(
                local_file=local_file,
                server=destination['sftp']['server'],
                port=destination['sftp']['port'],
                username=str(destination['sftp']['username']),
                password=self._global_func.get_destination_password(destination['sftp'], 'jobs', name),
                remote_path=os.path.join(destination['sftp']['path'], name)
            )
