# Imports
import traceback
import datetime
import flask

# Class
class API:
    def __init__(self, log, scheduler, job_status, alerts):
        self._log = log

        self._scheduler = scheduler
        self._job_status = job_status
        self._alerts = alerts

    def health(self):
        try:
            return flask.jsonify({
                'success': True
            }), 200
        except Exception as ex:
            self._log.error(f'There is a problem with /api/health API endpoint! Reason: {str(ex)}\n{traceback.format_exc()}')
            return flask.jsonify({
                'reason': f'There is a problem with /api/health API endpoint! Please see logs for details.'
            }), 500
    
    def jobs_list(self):
        try:
            data = {
                'success': True,
                'jobs': []
            }

            for job in self._scheduler.get_jobs():
                data['jobs'].append({
                    'name': job.id,
                    'active': job and job.next_run_time is not None,
                    'next_run': job.next_run_time,
                    'status': self._job_status[job.id]
                })

            return flask.jsonify(data), 200
        except Exception as ex:
            self._log.error(f'There is a problem with /api/jobs API endpoint! Reason: {str(ex)}\n{traceback.format_exc()}')
            return flask.jsonify({
                'reason': f'There is a problem with /api/jobs API endpoint! Please see logs for details.'
            }), 500

    def jobs_start(self, job_name):
        try:
            job = self._scheduler.get_job(job_name)

            # Check if job ID exists
            if not job:
                return flask.jsonify({
                    'reason': f'Job {job_name} does not exist!'
                }), 400

            # Check if job is active
            if not (job and job.next_run_time is not None):
                return flask.jsonify({
                    'reason': f'Job {job_name} is not active! Please check logs for more details.'
                }), 400

            # Check if job is running
            if self._job_status[job.id] == 'running':
                return flask.jsonify({
                    'reason': f'Job {job_name} is already running! Please wait till its done.'
                }), 400

            # Start job
            job.modify(next_run_time=datetime.datetime.now())
            self._log.info(f'Manually started {job_name} job!')

            return flask.jsonify({
                'success': True
            }), 201
        except Exception as ex:
            self._log.error(f'There is a problem with /api/jobs/{job_name}/start API endpoint! Reason: {str(ex)}\n{traceback.format_exc()}')
            return flask.jsonify({
                'reason': f'There is a problem with /api/jobs/{job_name}/start API endpoint! Please see logs for details.'
            }), 500

    def alerts_list(self):
        data = {
            'success': True,
            'alerts': self._alerts.list()
        }

        return flask.jsonify(data), 200

    def alerts_test(self, alert_name):
        try:
            alert = self._alerts.get(alert_name)

            # Check if alert ID exists
            if not alert:
                return flask.jsonify({
                    'reason': f'Alert {alert_name} does not exist!'
                }), 400

            # Run alert test
            alert.test()

            return flask.jsonify({
                'success': True
            }), 201
        except Exception as ex:
            self._log.error(f'There is a problem with /api/alerts/{alert_name}/test API endpoint! Reason: {str(ex)}\n{traceback.format_exc()}')
            return flask.jsonify({
                'reason': f'There is a problem with /api/alerts/{alert_name}/test API endpoint! Please see logs for details.'
            }), 500
