# Imports
from bin.services.destinations.local_destination import LocalDestination
from bin.services.destinations.sftp_destination import SFTPDestination
from bin.services.alerts.notifiers_alert import NotifierAlert
from bin.services.alerts.webhook_alert import WebhookAlert
from bin.services.jobs.postgresql_job import PostgreSQLJob
from bin.services.jobs.mysql_job import MySQLJob
from bin.services.jobs.mongodb_job import MongoDBJob
from bin.services.jobs.files_job import FilesJob
import bin.config
import logging
import os

# Attributes
cfg = bin.config.Config()
log = logging.getLogger(cfg.NAME)

# Functions
def get_alert_service(alert):
    if alert.config.keys()[0].lower() == 'webhook':
        return WebhookAlert(alert)
    if alert.config.keys()[0].lower() == 'notifier':
        return NotifierAlert(alert)

def get_destination_service(destination):
    if destination.config.keys()[0].lower() == 'local':
        return LocalDestination(destination)
    if destination.config.keys()[0].lower() == 'sftp':
        return SFTPDestination(destination)

def get_job_service(job):
    if job.config.keys()[0].lower() == 'postgresql':
        return PostgreSQLJob(job)
    if job.config.keys()[0].lower() == 'mysql':
        return MySQLJob(job)
    if job.config.keys()[0].lower() == 'mongodb':
        return MongoDBJob(job)
    if job.config.keys()[0].lower() == 'files':
        return FilesJob(job)

def _get_secrets_from_env(_type, name):
    ENV_VARIABLE_TEMPLATE = f'HAWK_BACKUP_{_type.upper()}__{name.upper()}__'

    found = []
    secrets = {}
    for env in os.environ:
        if env.upper().startswith(ENV_VARIABLE_TEMPLATE):
            found.append(env)
            secrets[env.upper().replace(ENV_VARIABLE_TEMPLATE, '').lower()] = os.environ.get(env)
    log.debug('Found {} environment variables starting with {}: {}'.format(len(found), ENV_VARIABLE_TEMPLATE, ','.join(found)))

    return secrets

def get_alert_secrets_from_env(name):
    return _get_secrets_from_env('alert', name)

def get_destination_secrets_from_env(name):
    return _get_secrets_from_env('destination', name)

def get_job_secrets_from_env(name):
    return _get_secrets_from_env('job', name)
