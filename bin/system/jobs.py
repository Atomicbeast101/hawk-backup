# Imports
from bin.error import APIError
from bin.system import db, log
import bin.validate
import bin.extract
from sqlalchemy.orm import validates, mapped_column, Mapped
import celery.result
import traceback
import safrs
import http

# Classes
class Job(db.Model, safrs.SAFRSBase):
    __tablename__ = 'jobs'

    id: Mapped[int] = mapped_column(primary_key=True)
    name = db.Column(db.Text, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)
    retention = db.Column(db.Text)
    alert_id: Mapped[int] = mapped_column(db.ForeignKey('alerts.id'))
    destination_id: Mapped[int] = mapped_column(db.ForeignKey('destinations.id'))
    config = db.Column(db.JSON, nullable=False)

    alert: Mapped['Alert'] = db.relationship()
    alert.expose = False
    destination: Mapped['Destination'] = db.relationship()
    destination.expose = False

    @validates('name')
    def validate_name(self, key, name):
        # Validate data
        if not name:
            raise ValueError('Attribute name value cannot be empty!')
        if not bin.validate.valid_name(name):
            raise ValueError('Attribute name must be letters only with optional _ symbol.')
        
        return name

    @validates('retention')
    def validate_retention(self, key, retention):
        # Validate data
        if retention:
            if not bin.validate.valid_retention(retention):
                raise ValueError('Attribute retention must be in #d format!')
            
        return retention

    @validates()
    def validate_all(self, key, value):
        # Validate config
        if not self.config:
            raise ValueError('Attribute config value cannot be empty!')
        status, response = bin.validate.valid_job_config(self)
        if not status:
            if response:
                raise ValueError(f'Attribute config is invalid for job! {response}')
            else:
                raise ValueError('Attribute config is invalid for job! Please check documentation on how to configure it.')

        # Test connection
        if not bin.extract.get_job_service(self).check():
            raise APIError(f'Unable to check connection to {self.name} job\'s source! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

        self.config = response

        return value

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def check(self):
        '''
            description : Check connection to source (database server, server on SSH, etc.)
        '''
        
        # Test connection
        if not bin.extract.get_job_service(self).check():
            raise APIError(f'Unable to check connection to {self.name} job\'s source! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

        return {}

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def start(self):
        '''
            description : Start a job
        '''
        
        # Start job
        try:
            job = bin.extract.get_job_service(self)
            # Make sure there isn't one running currently
            if job.is_running():
                raise APIError('There is already an active backup running for this job! Please cancel or wait till it finishes.', status_code=http.HTTPStatus.BAD_REQUEST.value)

            # Start task
            task = job.delay()
            return {
                'task': task.id
            }

        except Exception as ex:
            log.error(f'Unable to start backup for {self.name} job! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')
            raise APIError(f'Unable to start backup for {self.name} job! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

    @safrs.jsonapi_rpc(http_methods=['GET'])
    def status(self):
        '''
            description : Current status of the job
        '''
        
        # Get data
        try:
            job = bin.extract.get_job_service(self)
            # Make sure there is one running
            if not job.is_running():
                raise APIError('There is no active backup running for this job!', status_code=http.HTTPStatus.BAD_REQUEST.value)

            # TODO: get task ID by name
            # TODO: return APIError if no active tasks (if value above is null)
            # TODO: return JSON of status details

        except Exception as ex:
            log.error(f'Unable to get status of backup for {self.name} job! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')
            raise APIError(f'Unable to get status of backup for {self.name} job! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def stop(self):
        '''
            description : Stop a job
        '''
        
        # Stop job
        try:
            job = bin.extract.get_job_service(self)
            # Make sure there isn't one running currently
            if not job.is_running():
                raise APIError('There is no active backup for this job!', status_code=http.HTTPStatus.BAD_REQUEST.value)

            # TODO: get task ID by name
            # TODO: return APIError if no active tasks (if value above is null)
            # TODO: cancel task and return success

        except Exception as ex:
            log.error(f'Unable to stop backup for {self.name} job! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')
            raise APIError(f'Unable to stop backup for {self.name} job! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)
