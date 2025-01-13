# Imports
import notifiers
import yamale
import pysftp
import yaml
import os

# Attributes
# Config Options
VERSION = os.environ['VERSION'] if os.environ.get('VERSION') else 'v0-alpha'
CONFIG_PATH = '/config/settings.yml'
CONFIG_SCHEMA_PATH = 'bin/schema.yml'
JOB_TYPES = [ 'postgresql', 'mysql', 'mongodb', 'files', 'ansible' ]
## Logging
LOG_TYPES = ['both', 'file', 'syslog']
LOG_TYPE = os.environ['HAWKUPS_LOG_TYPE'] if os.environ.get('HAWKUPS_LOG_TYPE') else 'file'
LOG_LEVEL = os.environ['HAWKUPS_LOG_LEVEL'] if os.environ.get('HAWKUPS_LOG_LEVEL') else 'DEBUG'
LOG_SERVER = os.environ['HAWKUPS_LOG_SERVER'] if os.environ.get('HAWKUPS_LOG_SERVER') else None
## PostgreSQL
POSTGRESQL_SQL_GET_LIST_OF_DATABASES = "SELECT datname FROM pg_database WHERE datname <> ALL ('{{{databases}}}') ORDER BY datname;"
POSTGRESQL_DEFAULT_EXCLUDES = [
    'template0',
    'template1',
    'postgres'
]
MYSQL_SQL_GET_LIST_OF_DATABASES = "SHOW DATABASES WHERE `Database` NOT IN ({databases});"
MYSQL_DEFAULT_EXCLUDES = [
    'information_schema',
    'mysql',
    'performance_schema',
    'sys'
]

# Class
class Config:
    def __init__(self, log, global_func):
        self._log = log
        self._global_func = global_func

    def validate(self, path):
        try:
            config = None

            # Check if file exists
            if not os.path.isfile(path):
                raise Exception(f'Configuration file {path} does not exist or exists as a file!')
            self._log.debug('Successfully validated that configuration file exists!')

            # Load YAML schema & contents
            try:
                raw_config = yamale.make_data(CONFIG_PATH)
                self._log.debug('Successfully loaded config data to YAML!')
            except Exception as ex:
                raise Exception(f'Unable to load configuration file as YAML! Reason: {str(ex)}')

            # Validate JSON schema
            schema = yamale.make_schema(CONFIG_SCHEMA_PATH)
            try:
                yamale.validate(schema, raw_config)
                with open(CONFIG_PATH, 'r') as f:
                    config = yaml.safe_load(f)
                self._log.debug('YAML configuration has been validated against schema!')
            except Exception as ex:
                raise Exception(f'Configuration file does not meet schema layout! Please check the configuration file and refer to documentation for details. Reason: {str(ex)}')

            # Validate destination and alert names exist for each job
            for job in config['jobs']:
                name = job['name']
                ## Confirm destination exists under destinations
                destination = job['destination']
                if destination not in [dest['name'] for dest in config['destinations']]:
                    raise Exception(f'Destination {destination} does not exist under "destinations" in configuration file! Please use an existing one or add one.')
                ## Confirm alert exists under alerts
                if 'alert' in job:
                    alert = job['alert']
                    if alert not in [alert['name'] for alert in config['alerts']]:
                        raise Exception(f'Alert {alert} does not exist under "alerts" in configuration file! Please use an existing one or add one.')

            # Check alert config (notifiers)
            for alert in config['alerts']:
                if 'notifiers' in alert:
                    name = alert['name']
                    typee = alert['notifiers']['type'].lower()
                    if typee in notifiers.all_providers():
                        notify = notifiers.get_notifier(typee)
                        # Required keys exists
                        data = alert['notifiers']['data']
                        data = self._global_func.get_alert_secrets(data, name)
                        data['message'] = '' # automatically gets added when notification is sent, left blank for config validation reasons
                        if all(key in data for key in notify.required['required']):
                            # Make sure optional keys are acceptable for this type of notification
                            for key in data:
                                if key not in notify.required['required']:
                                    if key not in notify.schema['properties']:
                                        attributes = ','.join([x for x in notify.schema['properties']])
                                        raise Exception(f'{typee} notifiers option for {name} only accepts the following attributes: {attributes}')
                        else:
                            attributes = ','.join(notify.required['required'])
                            raise Exception(f'Minimum attributes are required to use {typee} notifiers option: {attributes}')
                    else:
                        types = ','.join(notifiers.all_providers())
                        raise Exception(f'{typee} is not supported for notifiers! Supported types: {types}')

            # Test destinations
            for dest in config['destinations']:
                name = dest['name']
                ### Test SFTP connection
                if 'sftp' in dest:
                    sftp_options = pysftp.CnOpts()
                    sftp_options.hostkeys = None
                    server = dest['sftp']['server']
                    port = dest['sftp']['port']
                    username = str(dest['sftp']['username'])
                    password = self._global_func.get_destination_password(dest['sftp'], 'destinations', name)
                    try:
                        with pysftp.Connection(server, port=port, username=username, password=password, cnopts=sftp_options):
                            self._log.debug(f'Successfully made a test connection to SFTP endpoint ({server}) [{name}]')
                    except Exception as ex:
                        raise Exception(f'Unable to connect to SFTP endpoint ({server}) [{name}]. Reason: {str(ex)}')
                ### TODO: more destination connections to test

            return True, config
        except Exception as ex:
            self._log.error(f'{str(ex)}')
        
        return False, None
