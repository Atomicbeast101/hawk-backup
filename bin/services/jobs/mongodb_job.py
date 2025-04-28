# Imports
from bin.services.jobs import log, BaseJob
import bin.extract
import celery.exceptions
import traceback
import pymongo
import zipfile
import bson
import os

# Class
class MongoDBJob(BaseJob):
    def __init__(self, job):
        super().__init__(job)

        self.name = f'mongodb-{job.name}'
        self._type = 'MongoDB'
        self._server = self._job.config['mongodb']['server']
        self._port = self._job.config['mongodb']['port']
        self._username = str(self._job.config['mongodb']['username'])
        self._password = bin.extract.get_job_secrets_from_env(job.name)['password'] if 'password' not in self._job.config else self._job.config['password']
        self._uri = f'mongodb://{self._username}:{self._password}@{self._server}:{self._port}/'
        self._excludes = self._job.config['mongodb']['excludes']
        self._destination = bin.extract.get_destination_service(self._job.destination)
        self._alert = bin.extract.get_alert_service(self._job.alert)

    def _get_connection(self):
        return pymongo.MongoClient(self._uri)

    def check(self):
        try:
            con = self._get_connection()
            con.admin.command('ping')

            return True
    
        except Exception as ex:
            log.warning(f'Unable to make a test connection to {self._server}:{self._port} {self._type} server! Reason: {str(ex)}')
            log.debug(traceback.format_exc())
            
        return False

    def _get_databases(self):
        databases = []
        try:
            con = self._get_connection()
            all_databases = con.list_database_names()
            for database in all_databases:
                if database not in self._excludes:
                    databases.append(database)
            log.debug(f'[{self._job.name}] Pulled {len(databases)} databases to backup!')
            return databases
    
        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to get list of databases from {self._server}:{self._port} {self._type} server!')

    # https://gist.github.com/Lh4cKg/939ce683e2876b314a205b3f8c6e8e9d
    def _dump(self, databases):
        try:
            con = self._get_connection()
            for database in databases:
                # excludes = ' '.join(['--excludeCollection={}'.format(exclude) for exclude in self._excludes])
                db = con[database]
                for collection in db.list_collection_names():
                    if not os.path.exists(self._temp_folder, database):
                        os.makedirs(os.path.exists(self._temp_folder, database))
                    with open(os.path.join(self._temp_folder, database, f'{collection}.bson')) as f:
                        for doc in db[collection].find():
                            f.write(bson.BSON.encode(doc))
                log.debug(f'[{self._job.name}] Backed up {database} from {self._server}:{self._port} {self._type} server so far...')

        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to dump database(s) from {self._server}:{self._port} {self._type} server to {self._temp_folder} folder! Reason: {str(ex)}')

    def _create_zip(self, backup_ts):
        zip_path = os.path.join(self._temp_folder, f'{backup_ts}.zip')

        try:
            with zipfile.ZipFile(zip_path, 'w') as zip:
                zip.write(os.path.join(self._temp_folder, 'collections.dump'))

        except Exception as ex:
            raise Exception(f'[{self._job.name}] Unable to put {self._type} database NoSQL file(s) to {zip_path}! Reason: {str(ex)}')

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
