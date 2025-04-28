# Imports
from bin.prometheus import Metrics
from bin.system.destinations import Destination
from bin.system.alerts import Alert
from bin.system.jobs import Job
from bin.system import db
import bin.extract
import bin.config
import prometheus_client
import celery.schedules
import flask_cors
import traceback
import logging
import warnings
import celery
import flask
import safrs
import sys
import os

# Attributes
config = bin.config.Config()
warnings.filterwarnings('ignore', '.*Failed to load HostKeys.*')
## Flask
application = flask.Flask(config.NAME)
application.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
flask_cors.CORS(application)
## Celery
celery_application = celery.Celery(
    config.NAME,
    broker=f'redis://{config.REDIS_SERVER}/1',
    backend=f'redis://{config.REDIS_SERVER}/2'
)

# Functions
def setup_log(config):
    log = None

    logFormatter = logging.Formatter('{"time":"%(asctime)s","type":"app","level":"%(levelname)s","message":"%(message)s"}')
    log = logging.getLogger()
    
    # Add console logging
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)
    
    # Add file logging if selected
    if 'file' in config.LOG_TYPES:
        fileHandler = logging.handlers.TimedRotatingFileHandler(
            os.path.join('/log', 'app.log'),
            when="d",
            interval=1,
            backupCount=10
        )
        fileHandler.setFormatter(logFormatter)
        log.addHandler(fileHandler)
    # Add syslog logging if selected
    if 'syslog' in config.LOG_TYPES:
        address = config.LOG_SYSLOG_HOST.split(':')[0]
        port = int(config.LOG_SYSLOG_HOST.split(':')[-1]) if ':' in config.LOG_SYSLOG_HOST else 514
        syslogHandler = logging.handlers.SysLogHandler(address=(address, port))
        syslogHandler.setFormatter(logFormatter)
        log.addHandler(syslogHandler)

    log.setLevel(config.LOG_LEVEL)

    return log

# Flask Functions
@application.route('/api/health', methods=['GET'])
def health():
    return flask.jsonify({
        'status': 'healthy',
        'version': config.VERSION
    })

if config.PROMETHEUS:
    @application.route('/metrics', methods=['GET'])
    def metrics():
        return flask.Response(prometheus_client.generate_latest(), mimetype=str('text/plain; version=0.0.4; charset=utf-8'))

# Main
def main():
    # Setup logging
    log = setup_log(config)

    try:
        log.info(f'Starting up hawk-backup {config.VERSION}...')

        # Setup flask
        application.secret_key = config.APP_SECRET_KEY

        # Build database
        with application.app_context():
            db.init_app(application)
            db.create_all()
            if config.API_DOCS:
                custom_swagger = {
                    'info': {
                        'title': 'Hawk-Backup API'
                    },
                    'securityDefinitions': {
                        'ApiKeyAuth': {
                            'type': 'apiKey',
                            'in': 'header',
                            'name': 'token'
                        }
                    }
                }
                api = safrs.SafrsApi(
                    application,
                    prefix='/api',
                    custom_swagger=custom_swagger,
                    schemes=[ 'http', 'https' ],
                    description='' # TODO: Maybe add something here?
                )
                for model in [Alert, Destination, Job]:
                    api.expose_object(model)

        # Validate configs in database
        # NOTE: Improve config validation before scheduling jobs to ensure database config didn't get changed while app was offline

        schedule = {}
        # Schedule backup jobs
        with application.app_context():
            for job in db.session.query(Job).all():
                if job.enabled:
                    task = bin.extract.get_job_service(job)
                    celery_application.register_task(task)
                    schedule[f'job-{job.name}'] = {
                        'task': task.name,
                        'schedule': celery.schedules.crontab(hour=0, minute=0) # NOTE: Improve this with DB-based configuration
                    }

        # Schedule cleanup jobs
        with application.app_context():
            for destination in db.session.query(Destination).all():
                task = bin.extract.get_destination_service(destination)
                celery_application.register_task(task)
                schedule[f'destination-{destination.name}'] = {
                    'task': task.name,
                    'schedule': celery.schedules.crontab(hour=0, minute=0) # NOTE: Improve this with DB-based configuration
                }
        
        # Start prometheus if enabled
        if config.PROMETHEUS:
            task = Metrics(celery_application)
            celery_application.register_task(task)
            schedule['metrics-updater'] = {
                'task': task.name,
                'schedule': celery.schedules.crontab(minute='*')
            }

        # Register schedule in celery
        celery_application.conf.beat_schedule = schedule

        log.info(f'hawk-backup {config.VERSION} ready to serve!')

    except Exception as ex:
        log.error(ex)
        log.debug(traceback.format_exc())
        exit(2)

if __name__ == 'app':
    main()
