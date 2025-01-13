# Imports
import notifiers
import requests

# Class
class Alert:
    def __init__(self, log, global_func, alert_name, config):
        self._log = log
        self._global_func = global_func
        self._alert_name = alert_name
        self._config = config

    def get_config(self):
        return self._config

    def _webhook(self, job_name, url, data):
        try:
            r = requests.post(url, data=data)
            if r.ok:
                self._log.info(f'Successfully made a webhook call to {url} for {job_name}!')
        except Exception as ex:
            raise Exception(f'Unable to make a webhook call to {url} for {job_name}! Reason: {str(ex)}')

    def _notifiers(self, job_name, typee, notify, data):
        try:
            notify.notify(**data)
            self._log.info(f'Successfully made a notifiers call to {typee} for {job_name}!')
        except Exception as ex:
            raise Exception(f'Unable to make a notifiers call to {typee} for {job_name}! Reason: {str(ex)}')

    def _navigate(self, job_name, message):
        # webhook
        if 'webhook' in self._config:
            data = self._config['webhook']['data']
            data = self._global_func.get_alert_secrets(data, self._alert_name)
            data['message'] = message
            self._webhook(job_name, self._config['webhook']['url'], data)

        # notifiers
        elif 'notifiers' in self._config:
            notification_type = self._config['notifiers']['type'].lower()
            data = self._config['notifiers']['data']
            data['message'] = message
            notify = notifiers.get_notifier(notification_type)
            self._notifiers(job_name, notification_type, notify, data)

    def test(self):
        self._navigate('test-alert', 'Made a test alert!')
        self._log.info(f'Made a test alert for {self._alert_name}!')

    def success(self, job_name):
        if self._config['success']:
            self._navigate(job_name, f'Successfully made backup for {job_name}!')
        else:
            self._log.debug(f'Skipping sending notification for {job_name} as "success" is set to disabled for {self._alert_name}.')

    def failed(self, job_name):
        if self._config['failure']:
            self._navigate(job_name, f'Unable made backup for {job_name}!')
        else:
            self._log.debug(f'Skipping sending notification for {job_name} as "failure" is set to disabled for {self._alert_name}.')

class Alerts:
    def __init__(self, log, global_func, config):
        self._log = log
        self._global_func = global_func

        self._alerts = self._generate_list(config)

    def _generate_list(self, config):
        alerts = {}

        for alert_config in config['alerts']:
            alerts[alert_config['name']] = Alert(self._log, self._global_func, alert_config['name'], alert_config)

        return alerts

    def list(self):
        data = []
        
        for alert_name in self._alerts:
            config = self._alerts[alert_name].get_config()
            sdata = {
                'name': alert_name,
                'success': config['success'],
                'failure': config['failure']
            }
            if 'webhook' in config:
                sdata['webhook_url'] = config['webhook']['url']
            elif 'notifiers' in config:
                sdata['notifiers_type'] = config['notifiers']['type']
            data.append(sdata)

        return data

    def get(self, alert_name):
        if alert_name in self._alerts:
            return self._alerts[alert_name]
        return None
