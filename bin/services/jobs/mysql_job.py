# Imports
from bin.services.jobs import log, config, BaseJob
import bin.extract
import celery.exceptions
import mysql.connector
import subprocess
import traceback
import zipfile
import os

# Class
class MySQLJob(BaseJob):
    def __init__(self, job):
        super().__init__(job)

        self.name = f'mysql-{job.name}'
        self._type = 'MySQL'
        self._server = self._job.config['mysql']['server']
        self._port = self._job.config['mysql']['port']
        self._username = str(self._job.config['mysql']['username'])
        self._password = bin.extract.get_job_secrets_from_env(job.name)['password'] if 'password' not in self._job.config else self._job.config['password']
        excludes = config.MYSQL_DEFAULT_EXCLUDES
        excludes.extend(self._job.config['mysql']['excludes'])
        self._excludes = ','.join(excludes)
        self._destination = bin.extract.get_destination_service(self._job.destination)
        self._alert = bin.extract.get_alert_service(self._job.alert)

    def _get_connection(self):
        return mysql.connector.connect(
            host=self._server,
            port=self._port,
            database='information_schema',
            user=self._username,
            password=self._password
        )

    def check(self):
        try:
            con = self._get_connection()
            cursor = con.cursor()
            cursor.execute('SELECT 1')

            return True
    
        except Exception as ex:
            log.warning(f'Unable to make a test connection to {self._server}:{self._port} {self._type} server! Reason: {str(ex)}')
            log.debug(traceback.format_exc())
            
        return False

    def _get_databases(self):
        try:
            con = self._get_connection()
            cursor = con.cursor()
            cursor.execute(config.MYSQL_SQL_GET_LIST_OF_DATABASES.format(excludes=','.join(["'{}'".format(exclude) for exclude in self._excludes])))
            databases = [row[0] for row in cursor.fetchall()]
            log.debug(f'[{self._job.name}] Pulled {len(databases)} databases to backup!')
            return databases

        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to get list of databases from {self._server}:{self._port} {self._type} server!')

    def _dump(self, databases):
        try:
            for database in databases:
                cmd = f'mysqldump --host={self._server} --port={self._port} --databases {database} --user={self._username} > {self._temp_folder}/{database}.sql'
                log.debug(f'[{self._job.name}] Executing following command: {cmd}')
                proc = subprocess.Popen(cmd, shell=True, env={ 'MYSQL_PWD': self._password }, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.wait()
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    raise Exception(stderr.decode())
                log.debug(f'[{self._job.name}] Backed up {database} from {self._server}:{self._port} {self._type} server so far...')

        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to dump database(s) from {self._server}:{self._port} {self._type} server to {self._temp_folder} folder! Reason: {str(ex)}')

    def _create_zip(self, backup_ts, databases):
        zip_path = os.path.join(self._temp_folder, f'{backup_ts}.zip')
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                for database in databases:
                    zip.write(os.path.join(self._temp_folder, f'{database}.sql'))
                    
        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to put {self._type} database SQL file(s) to {zip_path}! Reason: {str(ex)}')

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

            # Get list of databases
            databases = self._get_databases()

            # Dump databases
            self._dump(databases)

            # Get timestamp to use for zip file name
            backup_ts = self._generate_backup_ts()

            # Combine databases into single zip file
            self._create_zip(backup_ts, databases)

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
