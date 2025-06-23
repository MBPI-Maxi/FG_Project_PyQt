from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
from os import getenv

load_dotenv()

url = URL.create(
    drivername=getenv("DB_DRIVER"),
    username=getenv("DB_USER"),
    host=getenv("DB_HOST"),
    database=getenv("DB_NAME"),
    port=getenv("DB_PORT"),
    password=getenv("DB_PASSWORD")
)

engine = create_engine(url)

is_connected = None
try:
    with engine.connect() as conn:
        is_connected = True
except OperationalError as e:
    is_connected = str(e)