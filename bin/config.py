# Imports
import logging
import secrets
import os

# Classes
class Config:
    ## General
    NAME = 'hawk-backup'
    VERSION = os.environ.get('VERSION', 'v0.0')
    
    ## Config Schemas
    ALERT_CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'success': { 'type': 'boolean', 'default': False },
            'failure': { 'type': 'boolean', 'default': True },
            'webhook': {
                'type': 'object',
                'properties': {
                    'url': { 'type': 'string', 'format': 'uri' },
                    'data': { 
                        'type': 'object'
                    }
                },
                'required': ['url']
            },
            'notifiers': {
                'type': 'object',
                'properties': {
                    'type': { 'type': 'string', 'minLength': 1 },
                    'data': { 'type': 'object' }
                },
                'required': ['type']
            }
        },
        'oneOf': [
            { 'required': ['webhook'] },
            { 'required': ['notifiers'] }
        ]
    }
    DESTINATION_CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'local': { 'type': 'object' },
            'sftp': {
                'type': 'object',
                'properties': {
                    'server': { 
                        'type': 'string', 
                        'oneOf': ['hostname', 'ipv4', 'ipv6'] 
                    },
                    'port': { 'type': 'integer', 'minimum': 1, 'maximum': 65535, 'default': 22 },
                    'username': { 'type': 'string', 'minLength': 1 },
                    'password': { 'type': 'string' },
                    'path': { 'type': 'string', 'pattern': '^(/[^/]+)+/?$' }
                },
                'required': ['server', 'path']
            }
        },
        'oneOf': [
            { 'required': ['local'] },
            { 'required': ['sftp'] }
        ]
    }
    JOB_CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'postgresql': {
                'type': 'object',
                'properties': {
                    'server': { 
                        'type': 'string', 
                        'oneOf': ['hostname', 'ipv4', 'ipv6'] 
                    },
                    'port': { 'type': 'integer', 'minimum': 1, 'maximum': 65535, 'default': 5432 },
                    'username': { 'type': 'string', 'minLength': 1 },
                    'password': { 'type': 'string' },
                    'ssl': { 
                        'type': 'string', 
                        'enum': ['disable', 'allow', 'prefer', 'require']
                    },
                    'excludes': { 
                        'type': 'array',
                        'items': { 'type': 'string' }
                    }
                },
                'required': ['server']
            },
            'mysql': {
                'type': 'object',
                'properties': {
                    'server': { 
                        'type': 'string', 
                        'oneOf': ['hostname', 'ipv4', 'ipv6'] 
                    },
                    'port': { 'type': 'integer', 'minimum': 1, 'maximum': 65535, 'default': 3306 },
                    'username': { 'type': 'string', 'minLength': 1 },
                    'password': { 'type': 'string' },
                    'excludes': { 
                        'type': 'array',
                        'items': { 'type': 'string' }
                    }
                },
                'required': ['server']
            },
            'mongodb': {
                'type': 'object',
                'properties': {
                    'server': { 
                        'type': 'string', 
                        'oneOf': ['hostname', 'ipv4', 'ipv6'] 
                    },
                    'port': { 'type': 'integer', 'minimum': 1, 'maximum': 65535, 'default': 27017 },
                    'username': { 'type': 'string', 'minLength': 1 },
                    'password': { 'type': 'string' },
                    # 'excludes': { 
                    #     'type': 'array',
                    #     'items': { 'type': 'string' }
                    # }
                },
                'required': ['server']
            },
            'files': {
                'type': 'object',
                'properties': {
                    'server': { 
                        'type': 'string', 
                        'oneOf': ['hostname', 'ipv4', 'ipv6'] 
                    },
                    'port': { 'type': 'integer', 'minimum': 1, 'maximum': 65535, 'default': 5432 },
                    'username': { 'type': 'string', 'minLength': 1 },
                    'password': { 'type': 'string' },
                    'paths': { 
                        'type': 'array',
                        'items': { 'type': 'string' }
                    }
                },
                'required': ['server', 'paths']
            }
        },
        'oneOf': [
            { 'required': ['postgresql'] },
            { 'required': ['mysql'] },
            { 'required': ['mongodb'] },
            { 'required': ['files'] }
        ]
    }

    ## Redis
    REDIS_SERVER = os.environ.get('REDIS_SERVER', 'localhost:6379')

    ## Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    if LOG_LEVEL not in logging.getLevelNamesMapping(): raise ValueError('Invalid LOG_LEVEL environment variable value! Allowed: {}'.format(','.join(logging.getLevelNamesMapping())))
    LOG_TYPES = os.environ.get('LOG_TYPES', 'console').lower().split(',')
    for log_type in LOG_TYPES:
        if log_type not in ['console', 'file', 'syslog']: raise ValueError('Invalid LOG_TYPES environment variable value! Allowed (can be multiple, separated by comma): {}'.format(','.join(['console', 'file', 'syslog'])))
    LOG_FILE_PATH = '/logs'
    if 'syslog' in LOG_TYPES:
        LOG_SYSLOG_HOST = os.environ.get('LOG_SYSLOG_HOST', 'localhost:514')

    ## Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:////data/hawk-backup.db')
    if len(DATABASE_URL) == 0: raise ValueError('Invalid DATABASE_URL environment variable value! Please ensure it follows SQLalchemy database URL format!')
    ### PostgreSQL
    POSTGRESQL_SQL_GET_LIST_OF_DATABASES = "SELECT datname FROM pg_database WHERE datname <> ALL ('{{{excludes}}}') ORDER BY datname;"
    POSTGRESQL_DEFAULT_EXCLUDES = [
        'template0',
        'template1',
        'postgres'
    ]
    ### MySQL/MariaDB
    MYSQL_SQL_GET_LIST_OF_DATABASES = "SHOW DATABASES WHERE `Database` NOT IN ({excludes});"
    MYSQL_DEFAULT_EXCLUDES = [
        'information_schema',
        'mysql',
        'performance_schema',
        'sys'
    ]

    ## Web Stuff
    APP_SECRET_KEY = os.environ.get('APP_SECRET_KEY', secrets.token_urlsafe(32))
    if len(APP_SECRET_KEY) == 0: raise ValueError('Invalid APP_SECRET_KEY environment variable value! Please populate it with something!')
    API_TOKEN = os.environ.get('API_TOKEN')
    PROMETHEUS = os.environ.get('PROMETHEUS', 'false').lower()
    if PROMETHEUS not in ['true', 'false']: raise ValueError('Invalid PROMETHEUS environment variable! Allowed: true,false')
    PROMETHEUS = True if PROMETHEUS == 'true' else False
    API_DOCS = os.environ.get('API_DOCS', 'false').lower()
    if API_DOCS not in ['true', 'false']: raise ValueError('Invalid API_DOCS environment variable! Allowed: true,false')
    API_DOCS = True if API_DOCS == 'true' else False

    ## Backup Options
    DESTINATION_LOCAL_PATH = '/backups'
