# Imports
from bin.service import Service
import bin.config
import mysql.connector
import subprocess
import traceback
import psycopg2
import zipfile
import os

# Classes
class PostgreSQL(Service):
    def __init__(self, log, global_func, name, config, job_config, alerts):
        super().__init__(log, global_func, name, config)

        self._type = 'PostgreSQL'
        self._config = config
        self._server = job_config['postgresql']['server']
        self._port = job_config['postgresql']['port']
        self._username = str(job_config['postgresql']['username'])
        self._password = self._global_func.get_job_password(job_config['postgresql'], name)
        self._ssl = job_config['postgresql']['ssl']
        excludes = bin.config.POSTGRESQL_DEFAULT_EXCLUDES
        excludes.extend(job_config['postgresql']['excludes'])
        self._excludes = ','.join(excludes)
        self._destination = self._get_destination(job_config['destination'])
        self._retention = self._convert_retention(job_config['retention']) if 'retention' in job_config else self._convert_retention(self._get_destination(job_config['destination'])['retention'])
        self._alert = None
        if 'alert' in job_config:
            self._alert = alerts.get(job_config['alert'].lower())

    def _get_databases(self):
        try:
            con = psycopg2.connect(
                host=self._server,
                port=self._port,
                database='postgres',
                user=self._username,
                password=self._password,
                sslmode=self._ssl
            )
            
            cursor = con.cursor()
            cursor.execute(bin.config.POSTGRESQL_SQL_GET_LIST_OF_DATABASES.format(databases=self._excludes))
            
            return [row[0] for row in cursor.fetchall()]
        except Exception as ex:
            raise Exception(f'Unable to get list of databases from {self._server}:{self._port} {self._type} server [{self._name}]! Reason: {str(ex)}')
    
    def _dump(self, databases):
        try:
            for database in databases:
                cmd = f'pg_dump --host={self._server} --port={self._port} --dbname={database} --username={self._username} --no-password --file={self._temp_folder}/{database}.sql'
                self._log.debug(f'Executing following command: {cmd}')
                proc = subprocess.Popen(cmd, shell=True, env={ 'PGPASSWORD': self._password }, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.wait()
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    raise Exception(stderr.decode())
                self._log.debug(f'Backed up {database} from {self._server}:{self._port} {self._type} server [{self._name}] so far...')
        except Exception as ex:
            raise Exception(f'Unable to dump database(s) from {self._server}:{self._port} {self._type} server to {self._temp_folder} folder [{self._name}]! Reason: {str(ex)}')
    
    def _create_zip(self, backup_ts, databases):
        zip_path = os.path.join(self._temp_folder, f'{backup_ts}.zip')
        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                for database in databases:
                    zip.write(os.path.join(self._temp_folder, f'{database}.sql'))
        except Exception as ex:
            raise Exception(f'Unable to put {self._type} database SQL file(s) to {zip_path} [{self._name}]! Reason: {str(ex)}')
    
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

    def backup(self, job_status):
        try:
            job_status[self._name] = 'running'

            # Create temp folder to dump SQL files to
            self._create_temp_folder()

            # Get list of databases to dump
            databases = self._get_databases()

            # Dump database(s) to temp folder
            self._dump(databases)

            # Generate backup timestamp to use for backup file(s)
            backup_ts = self._generate_backup_ts()

            # Compress dumped files into zip file
            self._create_zip(backup_ts, databases)

            # Upload zip file to destination
            self._upload(backup_ts)

            # Cleanup temp folder
            self._cleanup_temp_folder()

            # Cleanup old zip backup files
            self._cleanup()

            self._alert.success(self._name)
            self._log.info(f'Successfully backed up {self._type} database: {self._name}!')
            job_status[self._name] = 'not_running'

        except Exception as ex:
            job_status[self._name] = 'failed'

            self._alert.failed(self._name)
            self._log.error(f'{str(ex)}\n{traceback.format_exc()}')
            # Cleanup temp folder to avoid data being left in /tmp after a failed backup
            self._cleanup_temp_folder()

class MySQL(Service):
    def __init__(self, log, global_func, name, config, job_config, alerts):
        super().__init__(log, global_func, name, config)

        self._type = 'MySQL'
        self._config = config
        self._server = job_config['mysql']['server']
        self._port = job_config['mysql']['port']
        self._username = str(job_config['mysql']['username'])
        self._password = self._global_func.get_job_password(job_config['mysql'], name)
        excludes = bin.config.MYSQL_DEFAULT_EXCLUDES
        excludes.extend(job_config['mysql']['excludes'])
        self._excludes = excludes
        self._destination = self._get_destination(job_config['destination'])
        self._retention = self._convert_retention(job_config['retention']) if 'retention' in job_config else self._convert_retention(self._get_destination(job_config['destination'])['retention'])
        self._alert = None
        if 'alert' in job_config:
            self._alert = alerts.get(job_config['alert'].lower())

    def _get_databases(self):
        try:
            con = mysql.connector.connect(
                host=self._server,
                port=self._port,
                database='information_schema',
                user=self._username,
                password=self._password
            )
            
            cursor = con.cursor()
            cursor.execute(bin.config.MYSQL_SQL_GET_LIST_OF_DATABASES.format(databases=','.join(["'{}'".format(exclude) for exclude in self._excludes])))
            
            return [row[0] for row in cursor.fetchall()]
        except Exception as ex:
            raise Exception(f'Unable to get list of databases from {self._server}:{self._port} {self._type} server [{self._name}]! Reason: {str(ex)}')

    def _dump(self, databases):
        try:
            for database in databases:
                cmd = f'mysqldump --host={self._server} --port={self._port} --databases {database} --user={self._username} > {self._temp_folder}/{database}.sql'
                self._log.debug(f'Executing following command: {cmd}')
                proc = subprocess.Popen(cmd, shell=True, env={ 'MYSQL_PWD': self._password }, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.wait()
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    raise Exception(stderr.decode())
                self._log.debug(f'Backed up {database} from {self._server}:{self._port} {self._type} server [{self._name}] so far...')
        except Exception as ex:
            raise Exception(f'Unable to dump database(s) from {self._server}:{self._port} {self._type} server to {self._temp_folder} folder [{self._name}]! Reason: {str(ex)}')

    def _create_zip(self, backup_ts, databases):
        zip_path = os.path.join(self._temp_folder, f'{backup_ts}.zip')
        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                for database in databases:
                    zip.write(os.path.join(self._temp_folder, f'{database}.sql'))
            return backup_ts
        except Exception as ex:
            raise Exception(f'Unable to put {self._type} database SQL file(s) to {zip_path} [{self._name}]! Reason: {str(ex)}')

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

    def backup(self, job_status):
        try:
            job_status[self._name] = 'running'

            # Create temp folder to dump SQL files to
            self._create_temp_folder()

            # Get list of databases to dump
            databases = self._get_databases()

            # Dump database(s) to temp folder
            self._dump(databases)

            # Generate backup timestamp to use for backup file(s)
            backup_ts = self._generate_backup_ts()

            # Compress dumped files into zip file
            self._create_zip(backup_ts, databases)

            # Upload zip file to destination
            self._upload(backup_ts)

            # Cleanup temp folder
            self._cleanup_temp_folder()

            # Cleanup old zip backup files
            self._cleanup()

            self._alert.success(self._name)
            self._log.info(f'Successfully backed up {self._type} database: {self._name}!')
            job_status[self._name] = 'not_running'

        except Exception as ex:
            job_status[self._name] = 'failed'

            self._alert.failed(self._name)
            self._log.error(f'{str(ex)}\n{traceback.format_exc()}')
            # Cleanup temp folder to avoid data being left in /tmp after a failed backup
            self._cleanup_temp_folder()

class MongoDB(Service):
    def __init__(self, log, global_func, name, config, job_config, alerts):
        super().__init__(log, global_func, name, config)

        self._type = 'MongoDB'
        self._config = config
        self._server = job_config['mongodb']['server']
        self._port = job_config['mongodb']['port']
        self._username = str(job_config['mongodb']['username'])
        self._password = self._global_func.get_job_password(job_config['mongodb'], name)
        self._excludes = job_config['mongodb']['excludes']
        self._destination = self._get_destination(job_config['destination'])
        self._retention = self._convert_retention(job_config['retention']) if 'retention' in job_config else self._convert_retention(self._get_destination(job_config['destination'])['retention'])
        self._alert = None
        if 'alert' in job_config:
            self._alert = alerts.get(job_config['alert'].lower())

    def _dump(self):
        try:
            excludes = ' '.join(['--excludeCollection={}'.format(exclude) for exclude in self._excludes])
            cmd = f'echo <hidden-password> | mongodump --host={self._server} --port={self._port} --username={self._username} {excludes} --archive > {self._temp_folder}/collections.dump'
            self._log.debug(f'Executing following command: {cmd}')
            proc = subprocess.Popen(cmd.replace('<hidden-password>', self._password), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise Exception(stderr.decode())
            self._log.debug(f'Backed up collections from {self._server}:{self._port} {self._type} server [{self._name}] so far...')
        except Exception as ex:
            raise Exception(f'Unable to dump database(s) from {self._server}:{self._port} {self._type} server to {self._temp_folder} folder [{self._name}]! Reason: {str(ex)}')

    def _create_zip(self, backup_ts):
        zip_path = os.path.join(self._temp_folder, f'{backup_ts}.zip')
        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                zip.write(os.path.join(self._temp_folder, f'collections.dump'))
            return backup_ts
        except Exception as ex:
            raise Exception(f'Unable to put {self._type} database NoSQL file(s) to {zip_path} [{self._name}]! Reason: {str(ex)}')

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

    def backup(self, job_status):
        try:
            job_status[self._name] = 'running'

            # Create temp folder to dump SQL files to
            self._create_temp_folder()

            # Dump database(s) to temp folder
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
            self._log.info(f'Successfully backed up {self._type} database: {self._name}!')
            job_status[self._name] = 'not_running'

        except Exception as ex:
            job_status[self._name] = 'failed'

            self._alert.failed(self._name)
            self._log.error(f'{str(ex)}\n{traceback.format_exc()}')
            # Cleanup temp folder to avoid data being left in /tmp after a failed backup
            self._cleanup_temp_folder()
