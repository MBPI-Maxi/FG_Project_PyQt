from sqlalchemy.orm import declarative_base

# this will be used for the rest of the based on the models
Base = declarative_base()

from .Endorsement import EndorsementModel, EndorsementModelT2
from .User import User, AuthLog