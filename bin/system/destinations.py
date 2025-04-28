# Imports
from bin.error import APIError
from bin.system import db, log
import bin.validate
import bin.extract
from sqlalchemy.orm import validates, mapped_column, Mapped
# from typing import List
import celery.result
import traceback
import safrs
import http

# Classes
class Destination(db.Model, safrs.SAFRSBase):
    __tablename__ = 'destinations'

    id: Mapped[int] = mapped_column(primary_key=True)
    name = db.Column(db.Text, nullable=False)
    retention = db.Column(db.Text, nullable=False)
    config = db.Column(db.JSON, nullable=False)

    # jobs: Mapped[List['Job']] = db.relationship()

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
        if not retention:
            raise ValueError('Attribute retention value cannot be empty!')
        if not bin.validate.valid_retention(retention):
            raise ValueError('Attribute retention must be in #d format!')
        
        return retention

    @validates()
    def validate_all(self, key, value):
        # Validate config
        if not self.config:
            raise ValueError('Attribute config value cannot be empty!')
        status, response = bin.validate.valid_destination_config(self)
        if not status:
            if response:
                raise ValueError(f'Attribute config is invalid for destination! {response}')
            else:
                raise ValueError('Attribute config is invalid for destination! Please check documentation on how to configure it.')

        # Test connection
        if not bin.extract.get_destination_service(self).check():
            raise APIError(f'Unable to check connection to {self.name} destination! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

        self.config = response

        return value

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def check(self):
        '''
            description : Health check of the destination target
        '''
        
        # Test connection
        if not bin.extract.get_destination_service(self).check():
            raise APIError(f'Unable to check connection to {self.name} destination! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

        return {}

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def cleanup(self):
        '''
            description : Cleanup old backups in destination target
        '''
        
        # Start cleanup
        try:
            destination = bin.extract.get_destination_service(self)
            # Make sure there isn't one running currently
            if destination.is_running():
                raise APIError('There is already an active cleanup running for this destination! Please cancel or wait till it finishes.', status_code=http.HTTPStatus.BAD_REQUEST.value)

            # Start task
            task = destination.delay()
            return {
                'task': task.id
            }

        except Exception as ex:
            log.error(f'Unable to start cleanup for {self.name} destination! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')
            raise APIError(f'Unable to start cleanup for {self.name} destination! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

    @safrs.jsonapi_rpc(http_methods=['GET'])
    def status(self):
        '''
            description : Check status of the cleanup of old backups in destination target
        '''
        
        # Get data
        try:
            destination = bin.extract.get_destination_service(self)
            # Make sure there is one running
            if not destination.is_running():
                raise APIError('There is no active cleanup running for this destination!', status_code=http.HTTPStatus.BAD_REQUEST.value)

            # TODO: get task ID by name
            # TODO: return APIError if no active tasks (if value above is null)
            # TODO: return JSON of status details

        except Exception as ex:
            log.error(f'Unable to get status of cleanup for {self.name} destination! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')
            raise APIError(f'Unable to get status of cleanup for {self.name} destination! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def stop(self):
        '''
            description : Stop the cleanup job
        '''
        
        # Stop cleanup
        try:
            destination = bin.extract.get_destination_service(self)
            # Make sure there isn't one running currently
            if not destination.is_running():
                raise APIError('There is no active cleanup for this destination!', status_code=http.HTTPStatus.BAD_REQUEST.value)

            # TODO: get task ID by name
            # TODO: return APIError if no active tasks (if value above is null)
            # TODO: cancel task and return success

        except Exception as ex:
            log.error(f'Unable to stop backup for {self.name} job! Reason: {str(ex)}')
            log.debug(f'{traceback.format_exc()}')
            raise APIError(f'Unable to stop backup for {self.name} job! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

