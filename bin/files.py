# Imports
from bin.service import Service
import traceback
import zipfile
import pysftp
import os

# Class
class Files(Service):
    def __init__(self, log, global_func, name, config, job_config, alerts):
        super().__init__(log, global_func, name, config)

        self._type = 'Files'
        self._config = config
        self._host = job_config['files']['host']
        self._port = job_config['files']['port']
        self._username = str(job_config['files']['username'])
        self._password = self._global_func.get_job_password(job_config['files'], name)
        self._paths = job_config['files']['paths']
        self._destination = self._get_destination(job_config['destination'])
        self._retention = self._convert_retention(job_config['retention']) if 'retention' in job_config else self._convert_retention(self._get_destination(job_config['destination'])['retention'])
        self._alert = None
        if 'alert' in job_config:
            self._alert = alerts.get(job_config['alert'].lower())
    
    def _dump(self):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
 
            with pysftp.Connection(self._host, port=self._port, username=self._username, password=self._password, cnopts=cnopts) as sftp:
                for path in self._paths:
                    try:
                        self._log.debug(f'Copying {self._host}:{self._port}{path} to {self._temp_folder}...')
                        if sftp.stat(path).st_mode & 0o40000:
                            sftp.get_r(path, self._temp_folder)
                        else:
                            filename = path.split('/')[-1]
                            sftp.get(path, os.path.join(self._temp_folder, filename))
                        self._log.debug(f'Backed up {path} files from {self._host}:{self._port} host [{self._name}] so far...')
                    except FileNotFoundError:
                        self._log.warning(f'Unable to find {path} in {self._host}:{self._port} host [{self._name}]!')
        except Exception as ex:
            raise Exception(f'Unable to copy files from {self._host}:{self._port} host to {self._temp_folder} folder [{self._name}]! Reason: {str(ex)}')

    def _create_zip(self, backup_ts):
        zip_file = f'{backup_ts}.zip'
        zip_path = os.path.join(self._temp_folder, zip_file)
        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                for file in os.listdir(self._temp_folder):
                    if str(file) != zip_file:
                        zip.write(os.path.join(self._temp_folder, str(file)))
        except Exception as ex:
            raise Exception(f'Unable to put files to {zip_path} [{self._name}]! Reason: {str(ex)}')

    def _upload(self, backup_ts):
        local_file = os.path.join(self._temp_folder, f'{backup_ts}.zip')
        try:
            self._uploader.run(self._name, local_file, self._destination)
        except Exception as ex:
            raise Exception(f'Unable to upload {local_file} to destination [{self._name}]! Reason: {str(ex)}')

    def _cleanup(self):
        try:
            self._cleanuper.run(self._name, self._retention, self._destination)
        except Exception as ex:
            raise Exception(f'Unable to prune old backups [{self._name}]! Reason: {str(ex)}')

    def backup(self):
        try:
            # Create temp folder to dump files to
            self._create_temp_folder()

            # Dump files to temp folder
            self._dump()

            # Generate backup timestamp to use for backup file(s)
            backup_ts = self._generate_backup_ts()

            # Compress dumped files into zip file
            self._create_zip(backup_ts)

            # Upload zip file to destination
            self._upload(backup_ts)

            # Cleanup temp folder
            self._cleanup_temp_folder()

            # Cleanup old zip backup files
            self._cleanup()

            self._alert.success(self._name)
            self._log.info(f'Successfully backed up {self._type.lower()}: {self._name}!')

        except Exception as ex:
            self._alert.failed(self._name)
            self._log.error(f'{str(ex)}\n{traceback.format_exc()}')
            # Cleanup temp folder to avoid data being left in /tmp after a failed backup
            self._cleanup_temp_folder()
