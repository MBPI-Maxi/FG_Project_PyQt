from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import os
import sys

print("--- STARTING DB CONFIGURATION ---")

# Determine if the application is a frozen executable
is_frozen = getattr(sys, 'frozen', False)
# print(f"Is application frozen (bundled)? {is_frozen}")

if is_frozen:
    # This is the code path for your bundled .exe
    application_path = os.path.dirname(sys.executable)
    # print(f"Application path determined from sys.executable: {application_path}")
    
    # This is the full path where we EXPECT to find the .env file
    dotenv_path = os.path.join(application_path, '.env')
    # print(f"Expecting .env file at: {dotenv_path}")
    
    # --- THIS IS THE MOST IMPORTANT CHECK ---
    # Does the file actually exist at that path?
    if os.path.exists(dotenv_path):
        # print("SUCCESS: .env file was FOUND at the expected path.")
        # Now, explicitly load it and check the result
        success = load_dotenv(dotenv_path=dotenv_path)
        # print(f"Result of load_dotenv command: {success}")
    else:
        print("!!! CRITICAL FAILURE: .env file was NOT FOUND at the expected path. !!!")
        
else:
    # This is the code path for running as a normal script (e.g., 'python main.py')
    # print("Running as a script, using standard load_dotenv().")
    load_dotenv()

# Check the value of the environment variable AFTER trying to load it
environment_value = os.getenv("ENVIRONMENT")
# print(f"Value of 'ENVIRONMENT' variable is: '{environment_value}'")

if environment_value == "MBPI":
    url = URL.create(
        drivername=os.getenv("DB_DRIVER"),
        username=os.getenv("DB_USER"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT"),
        password=os.getenv("DB_PASSWORD")
    )
    prodcode_db = URL.create(
        drivername=os.getenv("DB_DRIVER_ALT_PRODCODE_DB"),
        username=os.getenv("DB_USER_ALT_PRODCODE_DB"),
        host=os.getenv("DB_HOST_ALT_PRODCODE_DB"),
        database=os.getenv("DB_NAME_ALT_PRODCODE_DB"),
        port=os.getenv("DB_PORT_ALT_PRODCODE_DB"),
        password=os.getenv("DB_PASSWORD_ALT_PRODCODE_DB")
    )
elif environment_value == "HOME":
    url = URL.create(
        drivername=os.getenv("DB_DRIVER_HOME"),
        username=os.getenv("DB_USER_HOME"),
        host=os.getenv("DB_HOST_HOME"),
        database=os.getenv("DB_NAME_HOME"),
        port=os.getenv("DB_PORT_HOME"),
        password=os.getenv("DB_PASSWORD_HOME")
    )
else:
    raise ValueError("Environment not valid.")

if prodcode_db:
    prodcode_engine = create_engine(prodcode_db)

engine = create_engine(url)
is_connected = None
is_prodcode_connected = None


try:
    with engine.connect() as conn:
        is_connected = True
    with prodcode_engine.connect() as prod_conn:
        is_prodcode_connected = True    
except OperationalError as e:
    is_connected = str(e)