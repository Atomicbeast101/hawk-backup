# Imports
import bin.config
import flask_sqlalchemy
import logging

# Attributes
config = bin.config.Config()
db = flask_sqlalchemy.SQLAlchemy()
log = logging.getLogger(config.NAME)
