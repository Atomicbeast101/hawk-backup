# Imports
import bin.databases
import bin.metrics
import bin.config
import bin.alerts
import bin.files
import bin.api
from apscheduler.schedulers.background import BackgroundScheduler
import logging.handlers
import warnings
import logging
import secrets
import string
import flask
import sys
import os

# Attributes
app = flask.Flask(__name__)
app.secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
AUTH_TYPES = ['basic', 'none']
## Ignoring warning on disabling host keys for SFTP connections
warnings.filterwarnings('ignore', '.*Failed to load HostKeys.*')

# Setup Logging
if bin.config.LOG_TYPE.lower() not in bin.config.LOG_TYPES:
    print('ERROR: Unable to start application due to invalid LOG_TYPE environment variable! Please choose the following: ')
    exit(0)
logFormatter = logging.Formatter('{"time":"%(asctime)s","type":"app","level":"%(levelname)s","message":"%(message)s"}')
log = logging.getLogger()
def getFileHandler():
    fileHandler = logging.handlers.TimedRotatingFileHandler(
        os.path.join('/log', 'app.log'),
        when="d",
        interval=1,
        backupCount=10
    )
    fileHandler.setFormatter(logFormatter)
    return fileHandler
def getSyslogHandler():
    address = bin.config.LOG_SERVER.split(':')[0]
    port = int(bin.config.LOG_SERVER.split(':')[-1]) if ':' in bin.config.LOG_SERVER else 514
    syslogHandler = logging.handlers.SysLogHandler(address=(address, port))
    syslogHandler.setFormatter(logFormatter)
    return syslogHandler
if bin.config.LOG_TYPE.lower() == 'both':
    log.addHandler(getFileHandler())
    log.addHandler(getSyslogHandler())
elif bin.config.LOG_TYPE.lower() == 'file':
    log.addHandler(getFileHandler())
elif bin.config.LOG_TYPE.lower() == 'syslog':
    log.addHandler(getSyslogHandler())
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)
log.setLevel(bin.config.LOG_LEVEL)

# Class
class GlobalFunctions:
    def __init__(self, log):
        self._log = log
    
    def _get_password(self, data, area, name):
        if 'password' in data:
            return str(data['password'])
        else:
            fixed_name = name.replace('-', '_')
            env = f'HAWKUPS_{area.upper()}__{fixed_name}__PASSWORD'
            if os.environ.get(env):
                return os.environ[env]
            else:
                raise Exception(f'"password" isn\'t set in settings.yml for {name} or "{env}" doesn\'t exist for it!')

    def get_destination_password(self, data, destination_name):
        return self._get_password(data, 'destinations', destination_name)

    def get_job_password(self, data, job_name):
        return self._get_password(data, 'jobs', job_name)

    def _get_envs(self, env_filter):
        envs = []

        for env in os.environ:
            if env.startswith(env_filter):
                envs.append(env)
        
        return envs

    def get_alert_secrets(self, data, alert_name):
        fixed_name = alert_name.replace('-', '_')
        envs = self._get_envs(f'HAWKUPS_ALERTS__{fixed_name}__')
        if len(envs) > 0:
            for env in envs:
                key = env.replace(f'HAWKUPS_ALERTS__{fixed_name}__', '').lower()
                data[key] = os.environ[env]
        return data

# Main
def main():
    log.info(f'Starting up Hawk Backup {bin.config.VERSION}...')

    global_func = GlobalFunctions(log)

    # Validate config
    config = bin.config.Config(log, global_func)
    status, config = config.validate(bin.config.CONFIG_PATH)
    if not status:
        exit(4)

    # Alerts
    alerts = bin.alerts.Alerts(log, global_func, config)

    # Jobs
    scheduler = BackgroundScheduler()
    for job_config in config['jobs']:
        name = job_config['name']
        if 'postgresql' in job_config:
            job = bin.databases.PostgreSQL(log, global_func, name, config, job_config, alerts)
            scheduler.add_job(job.backup, 'cron', hour=0, minute=0, id=name)
        elif 'mysql' in job_config:
            job = bin.databases.MySQL(log, global_func, name, config, job_config, alerts)
            scheduler.add_job(job.backup, 'cron', hour=0, minute=0, id=name)
        elif 'mongodb' in job_config:
            job = bin.databases.MongoDB(log, global_func, name, config, job_config, alerts)
            scheduler.add_job(job.backup, 'cron', hour=0, minute=0, id=name)
        elif 'files' in job_config:
            job = bin.files.Files(log, global_func, name, config, job_config, alerts)
            scheduler.add_job(job.backup, 'cron', hour=0, minute=0, id=name)
        else:
            log.warning(f'Unrecognized backup type for {name}, ignoring...')
    scheduler.start()

    # API
    api = bin.api.API(log, scheduler, alerts)
    app.add_url_rule('/api/health', view_func=api.health, methods=['GET'])
    app.add_url_rule('/api/jobs', view_func=api.jobs_list, methods=['GET'])
    app.add_url_rule('/api/jobs/<job_name>/start', view_func=api.jobs_start, methods=['POST'])
    # app.add_url_rule('/api/jobs/<job_name>/status', view_func=api.jobs_status, methods=['GET'])
    app.add_url_rule('/api/alerts', view_func=api.alerts_list, methods=['GET'])
    app.add_url_rule('/api/alerts/<alert_name>/test', view_func=api.alerts_test, methods=['POST'])

    # Prometheus
    if config['system']['prometheus']['enabled']:
        metrics = bin.metrics.Metrics(log, config['system']['prometheus']['port'], scheduler)
        metrics.start()

    log.info(f'Hawk Backup {bin.config.VERSION} ready to serve!')

    # For local testing
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080)

main()
