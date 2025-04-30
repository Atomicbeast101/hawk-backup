# Imports
from bin.system.destinations import Destination
from bin.system.alerts import Alert
from bin.system.jobs import Job
import bin.config
import prometheus_client
import sqlalchemy.pool
import traceback
import logging
import celery.exceptions
import celery

# Attributes
config = bin.config.Config()
log = logging.getLogger(config.NAME)

# Class
class Metrics(celery.Task):
    def __init__(self, celery_application):
        self.name = 'metrics-updater'
        self._db = sqlalchemy.create_engine(config.DATABASE_URL, poolclass=sqlalchemy.pool.NullPool)
        self._metrics = {
            'info': prometheus_client.Info('hawk_backup_version', 'Build version', ['version']),
            'alert': prometheus_client.Info('hawk_backup_alert', 'Details of alert', ['id', 'name', 'type']),
            'destination': prometheus_client.Info('hawk_backup_destination', 'Details of destination', ['id', 'name', 'retention', 'type', 'jobs']),
            'destination_cleanup_status': prometheus_client.Gauge('hawk_backup_destination_cleanup_status', 'Status of destination\'s cleanup', ['id']),
            'destination_cleanup_next_run_timestamp': prometheus_client.Gauge('hawk_backup_destination_cleanup_next_run_timestamp', 'Timestamp of next cleanup job for destination', ['id']),
            'job': prometheus_client.Info('hawk_backup_job', 'Details of job', ['id', 'name', 'type', 'destination_id', 'destination_name', 'alert_id', 'alert_name']),
            'job_status': prometheus_client.Gauge('hawk_backup_job_status', 'Status of backup job', ['id']),
            'job_next_run_timestamp': prometheus_client.Gauge('hawk_backup_job_next_run_timestamp', 'Timestamp of next run for backup job', ['id'])
        }
        self._metrics['info'].labels(version=config.VERSION)

        self._celery_application = celery_application

    def _get_task(self, name):
        return self._celery_application.tasks.get(name)

    def run(self):
        self.update_state(state='RUNNING', meta={})

        try:
            # Update alert metrics
            for alert in self._db.session.query(Alert).all():
                self._metrics['alert'].labels(
                    id=alert.id, 
                    name=alert.name, 
                    type=alert.config.keys()[0].lower()
                )
            
            # Update destination metrics
            for destination in self._db.session.query(Destination).all():
                self._metrics['destination'].labels(
                    id=destination.id, 
                    name=destination.name,
                    retention=destination.retention,
                    type=destination.config.keys()[0].lower(),
                    # jobs=self._db.session.query(Job).filter(Job.destination_id == destination.id).count()
                )
                task = self._get_task(f'{destination.config.keys()[0].lower()}-{destination.name}')
                log.debug(f'Destination task found for {destination.name}: {task}')
                # TODO: Get celery status of destination cleanup status
                # TODO: Get timestamp of next run for destination cleanup

            # Update job metrics
            for job in self._db.session.query(Job).all():
                self._metrics['job'].labels(
                    id=job.id, 
                    name=job.name,
                    type=job.config.keys()[0].lower(),
                    destination_id=job.destination.id,
                    destination_name=job.destination.name,
                    alert_id=job.alert.id,
                    alert_name=job.alert.name
                )
                task = self._get_task(f'{job.config.keys()[0].lower()}-{job.name}')
                log.debug(f'Job task found for {job.name}: {task}')
                # TODO: Get celery status of job backup status
                # TODO: Get timestamp of next run for job backup

        except Exception as ex:
            log.error(f'Unable to update Prometheus metrics! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')

        self.update_state(state='UPDATED', meta={})

        raise celery.exceptions.Ignore()
