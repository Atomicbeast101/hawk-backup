# Imports
import prometheus_client
import threading
import traceback
import time

# Class
class Metrics(threading.Thread):
    def __init__(self, log, port, scheduler):
        super().__init__()
        
        self._log = log

        self._port = port
        self._scheduler = scheduler

        self._job_active = prometheus_client.Gauge('hawkbackup_job_active', 'Status of active job', ['id'])
        self._job_next_run = prometheus_client.Gauge('hawkbackup_job_next_run_timestamp', 'Job\'s next run timestamp', ['id'])
    
    def _update(self):
        for job in self._scheduler.get_jobs():
            self._job_active.labels(id=job.id).set(job and job.next_run_time is not None)
            self._job_next_run.labels(id=job.id).set(job.next_run_time.timestamp())

    def run(self):
        prometheus_client.start_http_server(self._port)
        self._log.info(f'Prometheus metrics has been exposed at http://0.0.0.0:{self._port}/metrics')

        while True:
            self._update()
            self._log.debug(f'Updated prometheus metrics!')
            time.sleep(5)
