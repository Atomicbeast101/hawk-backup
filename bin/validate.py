# Imports
import bin.extract
import bin.config
import jsonschema
import notifiers
import celery
import re

# Attributes
cfg = bin.config.Config()

# Functions
def valid_name(name):
    return re.match(r'^[A-Za-z_]+$', name) # Only accept A-Z, a-z & _

def valid_retention(retention):
    return re.match(r'^[0-9]+(d)$', retention) # Only accepts days for now

def _valid_config(config, SCHEMA):
    try:
        jsonschema.validate(config, SCHEMA)
        return True, config
    except jsonschema.ValidationError:
        return False, None

def valid_alert_config(alert):
    # Validate original config
    status, config_with_defaults = _valid_config(alert.config, cfg.ALERT_CONFIG_SCHEMA)

    # Validate config w/ defaults & secrets from ENV
    config_with_secrets = config_with_defaults
    if status:
        # Load from ENV
        config_with_secrets.update(bin.extract.get_alert_secrets_from_env(alert.name))
        status, config_with_secrets = _valid_config(alert.config, cfg.ALERT_CONFIG_SCHEMA)

    # Check to make sure config w/ defaults & secrets have everything that's needed
    if status:
        if config_with_secrets.keys()[0] == 'notifiers':
            # Check if valid notifier type
            if not config_with_secrets['notifiers']['type'].lower() in notifiers.all_providers():
                return False, 'Unknown {} notifier type! Allowed: {}'.format(config_with_secrets['notifiers']['type'].lower(), ','.join(notifiers.all_providers()))

            # Check if ENV variables are populated for specific notifier type
            notify = notifiers.get_notifier(config_with_secrets['notifiers']['type'].lower())

            ## Required attributes exists
            if not all(required_key in config_with_secrets for required_key in notify.required['required']):
                return False, 'Missing required config attributes for {} notifier type! Required: {}. Perhaps it wasn\'t set properly in environment varible(s)!'.format(config_with_secrets['notifiers']['type'].lower(), ','.join(notify.required['required']))
            ## Optional attributes are accepted
            if not all(optional_key in notify.schema['properties'] for optional_key in config_with_secrets):
                return False, 'Invalid optional config attribute for {} notifier type! All attributes permitted: {} notifier type! Required: {}. Perhaps it wasn\'t set properly in environment varible(s)!'.format(config_with_secrets['notifiers']['type'].lower(), ','.join([x for x in notify.schema['properties']]))

    return status, config_with_defaults

def valid_destination_config(destination):
    # Validate original config
    status, config_with_defaults = _valid_config(destination.config, cfg.DESTINATION_CONFIG_SCHEMA)

    # Validate config w/ defaults & secrets from ENV
    config_with_secrets = config_with_defaults
    if status:
        # Load from ENV
        config_with_secrets.update(bin.extract.get_destination_secrets_from_env(destination.name))
        status, config_with_secrets = _valid_config(destination.config, cfg.DESTINATION_CONFIG_SCHEMA)

    # Check to make sure config w/ defaults & secrets have everything that's needed
    if status:
        if config_with_secrets.keys()[0] == 'sftp':
            if 'password' not in config_with_secrets['sftp']:
                return False, 'Missing password credentials in config! Perhaps it wasn\'t set properly in environment varible!'
    
    return status, config_with_defaults

def valid_job_config(job):
    # Validate original config
    status, config_with_defaults = _valid_config(job.config, cfg.JOB_CONFIG_SCHEMA)

    # Validate config w/ defaults & secrets from ENV
    config_with_secrets = config_with_defaults
    if status:
        # Load from ENV
        config_with_secrets.update(bin.extract.get_job_secrets_from_env(job.name))
        status, config_with_secrets = _valid_config(job.config, cfg.JOB_CONFIG_SCHEMA)

    # Check to make sure config w/ defaults & secrets have everything that's needed
    if status:
        if config_with_secrets.keys()[0] in ['postgresql', 'mysql', 'mongodb', 'files']:
            if not 'password' in config_with_secrets['sftp']:
                return False, 'Missing password credentials in config! Perhaps it wasn\'t set properly in environment varible!'
    
    return status, config_with_defaults
