from config.db import is_connected, engine
from models import Base

# this should be imported so Base(declarative_base) will able to read the EndorsementModel
def import_models():
    from models.Endorsement import EndorsementModel

if __name__ == "__main__":
    if is_connected == True:
        print("Database is connected.")

        # import the models here
        import_models()

        # create the tables using this commands
        # Base.metadata.create_all(engine)

        # load the login application here


    else:
        print(f"Failed to connect to the database: {is_connected}")
