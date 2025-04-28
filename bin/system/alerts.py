# Imports
from bin.system import db
import bin.validate
import bin.extract
import bin.error
from sqlalchemy.orm import validates, mapped_column, Mapped
from typing import List
import safrs
import http

# Classes
class Alert(db.Model, safrs.SAFRSBase):
    __tablename__ = 'alerts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name = db.Column(db.Text, nullable=False)
    notify_success = db.Column(db.Boolean, nullable=False)
    notify_failure = db.Column(db.Boolean, nullable=False)
    config = db.Column(db.JSON, nullable=False)

    # jobs: Mapped[List['Job']] = db.relationship()

    @validates('name')
    def validate_name(self, key, value):
        # Validate data
        if not value:
            raise ValueError('Attribute name value cannot be empty!')
        if not bin.validate.valid_name(value):
            raise ValueError('Attribute name must be letters only with optional _ symbol.')
        
        return value

    @validates('notify_success')
    def validate_notify_success(self, key, value):
        # Validate data
        if not value:
            raise ValueError('Attribute notify_success value cannot be empty!')
        if not isinstance(value, bool):
            raise ValueError('Attribute notify_success value must be boolean (true/false)!')

    @validates('notify_failure')
    def validate_notify_success(self, key, value):
        # Validate data
        if not value:
            raise ValueError('Attribute notify_failure value cannot be empty!')
        if not isinstance(value, bool):
            raise ValueError('Attribute notify_failure value must be boolean (true/false)!')

    @validates()
    def validate_all(self, key, value):
        # Validate config
        if not self.config:
            raise ValueError('Attribute config value cannot be empty!')
        status, response = bin.validate.valid_alert_config(self)
        if not status:
            if response:
                raise ValueError(f'Attribute config is invalid for alert! {response}')
            else:
                raise ValueError('Attribute config is invalid for alert! Please check documentation on how to configure it.')
            
        # Test connection
        if not bin.extract.get_alert_service(self).test():
            raise bin.error.APIError(f'Unable to perform test notification for {self.name} {self.config.keys()[0].lower()} alert! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

        self.config = response

        return value

    @safrs.jsonapi_rpc(http_methods=['POST'])
    def test(self):
        '''
            description : Test alert
        '''

        # Test connection
        if not bin.extract.get_alert_service(self).test():
            raise bin.error.APIError(f'Unable to perform test for {self.name} alert! Please see logs for details.', status_code=http.HTTPStatus.BAD_REQUEST.value)

        return {}
