# Imports
from bin.services.jobs import log, BaseJob
import bin.extract
import celery.exceptions
import traceback
import zipfile
import pysftp
import os

# Class
class FilesJob(BaseJob):
    def __init__(self, job):
        super().__init__(job)

        self.name = f'files-{job.name}'
        self._type = 'Files'
        self._host = self._job.config['files']['host']
        self._port = self._job.config['files']['port']
        self._username = str(self._job.config['files']['username'])
        self._password = bin.extract.get_job_secrets_from_env(job.name)['password'] if 'password' not in self._job.config else self._job.config['password']
        self._paths = self._job.config['files']['paths']
        self._destination = bin.extract.get_destination_service(self._job.destination)
        self._alert = bin.extract.get_alert_service(self._job.alert)

    def _dump(self):
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
 
            with pysftp.Connection(self._host, port=self._port, username=self._username, password=self._password, cnopts=cnopts) as sftp:
                for path in self._paths:
                    try:
                        log.debug(f'[{self._job.name}] Copying {self._host}:{self._port}{path} to {self._temp_folder}...')
                        if sftp.stat(path).st_mode & 0o40000:
                            sftp.get_r(path, self._temp_folder)
                        else:
                            filename = path.split('/')[-1]
                            sftp.get(path, os.path.join(self._temp_folder, filename))
                        log.debug(f'[{self._job.name}] Backed up {path} files from {self._host}:{self._port} host so far...')
                    except FileNotFoundError:
                        log.warning(f'[{self._job.name}] Unable to find {path} path in {self._host}:{self._port} host!')
                        
        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to copy files from {self._host}:{self._port} host to {self._temp_folder} folder! Reason: {str(ex)}')

    def _create_zip(self, backup_ts):
        zip_file = f'{backup_ts}.zip'
        zip_path = os.path.join(self._temp_folder, zip_file)

        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                for file in os.listdir(self._temp_folder):
                    if str(file) != zip_file:
                        zip.write(os.path.join(self._temp_folder, str(file)))

        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to zip file(s) to {zip_path}! Reason: {str(ex)}')

    def _upload(self, backup_ts):
        local_file = os.path.join(self._temp_folder, f'{backup_ts}.zip')

        try:
            self._destination.upload(data={
                'local_file': local_file
            })

        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to upload {local_file} to {self._destination.name} destination! Reason: {str(ex)}')

    def run(self):
        self.update_state(state='RUNNING', meta={})
        
        try:
            # Create temp folder
            self._create_temp_folder()

            # Dump databases
            self._dump()

            # Get timestamp to use for zip file name
            backup_ts = self._generate_backup_ts()

            # Combine databases into single zip file
            self._create_zip(backup_ts)

            # Upload
            self._upload(backup_ts)

            # Cleanup temp folder
            self._cleanup_temp_folder()

            if not self._alert.success(self._job):
                raise Exception(f'[{self._job.name}] Unable to send success alert to {self._alert.name} alert!')
            
            log.info(f'Successfully backed up {self._job.name} {self._type}!')
            self.update_state(state='SUCCESS', meta={})

        except Exception as ex:
            log.error(f'{str(ex)}')
            log.debug(f'{traceback.format_exc}')
            if not self._alert.failure(self._job):
                log.error(f'[{self._job.name}] Unable to send failure alert to {self._alert.name}')
            self.update_state(state='ERROR', meta={})

        raise celery.exceptions.Ignore()
