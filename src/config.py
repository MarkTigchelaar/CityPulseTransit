import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

# Fail loud and fast on boot
POSTGRES_USER=os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB=os.getenv("POSTGRES_DB")
DB_SCHEMA=os.getenv("DB_SCHEMA")
POSTGRES_PORT=os.getenv("POSTGRES_PORT")
HOST_NAME=os.getenv("HOST_NAME")
KAFKA_BROKER_PORT=os.getenv("KAFKA_BROKER_PORT")
DB_CONNECTION=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{HOST_NAME}:{POSTGRES_PORT}/{POSTGRES_DB}"
