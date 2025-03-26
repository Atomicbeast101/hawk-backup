# Imports
import bin.config
import prometheus_client
import threading
import flask
import time

# Class
# https://gist.github.com/ruanbekker/e5b1e7895f62b020ff29b5f40767190c
class Metrics:
    def __init__(self, log, scheduler):
        self._log = log
        self._scheduler = scheduler

        self._metrics = {
            'info': prometheus_client.Info('hawkbackup_version', 'Build version', ['version']),
            'job_active': prometheus_client.Gauge('hawkbackup_job_active', 'Status of active job', ['id']),
            'job_next_run': prometheus_client.Gauge('hawkbackup_job_next_run_timestamp', 'Job\'s next run timestamp', ['id'])
        }
        self._metrics['info'].labels(version=bin.config.VERSION)
        MetricsUpdater(log, scheduler, self._metrics).start()

    def metrics(self):
        return flask.Response(prometheus_client.generate_latest(), mimetype=str('text/plain; version=0.0.4; charset=utf-8'))

class MetricsUpdater(threading.Thread):
    def __init__(self, log, scheduler, metrics):
        super().__init__()
        
        self._log = log
        self._scheduler = scheduler
        self._metrics = metrics

    def _update(self):
        for job in self._scheduler.get_jobs():
            self._metrics['job_active'].labels(id=job.id).set(job and job.next_run_time is not None)
            self._metrics['job_next_run'].labels(id=job.id).set(job.next_run_time.timestamp())

    def run(self):
        self._log.info(f'Prometheus metrics has been exposed at /metrics')

        while True:
            self._update()
            self._log.debug(f'Updated prometheus metrics!')
            time.sleep(5)
