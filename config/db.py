from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from os import getenv

load_dotenv()

if getenv("ENVIRONMENT") == "MBPI":
    url = URL.create(
        drivername=getenv("DB_DRIVER"),
        username=getenv("DB_USER"),
        host=getenv("DB_HOST"),
        database=getenv("DB_NAME"),
        port=getenv("DB_PORT"),
        password=getenv("DB_PASSWORD")
    )
elif getenv("ENVIRONMENT") == "HOME":
    url = URL.create(
        drivername=getenv("DB_DRIVER_HOME"),
        username=getenv("DB_USER_HOME"),
        host=getenv("DB_HOST_HOME"),
        database=getenv("DB_NAME_HOME"),
        port=getenv("DB_PORT_HOME"),
        password=getenv("DB_PASSWORD_HOME")
    )
else:
    raise ValueError("Environment not valid.")

engine = create_engine(url)

is_connected = None
try:
    with engine.connect() as conn:
        is_connected = True
except OperationalError as e:
    is_connected = str(e)