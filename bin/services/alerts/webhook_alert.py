# Imports
from bin.services.alerts import BaseAlert
import bin.extract
import bin.error
import requests

# Class
class WebhookAlert(BaseAlert):
    def __init__(self, alert):
        super().__init__(alert)

        self._log_alert_type = f'{self._alert.name} webhook alert'

        self._data = self._alert.config['webhook']['data']
        self._data.update(bin.extract.get_alert_secrets_from_env(self._alert.name))   

    def _send(self, message):
        try:
            # Get data
            self._data['message'] = message

            # Send alert
            r = requests.post(self._alert.config['webhook']['url'], json=self._data)
            
            return r.ok

        except Exception as ex:
            raise bin.error.AlertError(f'Unexpected error when trying to send a notification to {self._log_alert_type}! Reason: {str(ex)}')

    def test(self):
        try:
            # Send alert
            if not self._send('Made a test alert!'):
                raise bin.error.AlertError(f'Unable to send a test notification to {self._log_alert_type}! Reason: {str(ex)}')
            
            return True

        except Exception as ex:
            return False
    
    def success(self, job):
        try:
            # Send alert
            if not self._send(f'Successfully made a backup for {job.name}'):
                raise bin.error.AlertError(f'Unable to send a success notification for {job.name} to {self._log_alert_type}! Reason: {str(ex)}')
            
            return True

        except Exception as ex:
            return False
    
    def failure(self, job):
        try:
            # Send alert
            if not self._send(f'Unable to make a backup for {job.name}'):
                raise bin.error.AlertError(f'Unable to send a failed notification for {job.name} to {self._log_alert_type}! Reason: {str(ex)}')
            
            return True

        except Exception as ex:
            return False
