from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('DATABASE_HOST')
USER = os.getenv('DATABASE_USER')
PASSWORD = os.getenv('DATABASE_PASSWORD')
NAME = os.getenv('DATABASE_NAME')
PORT = os.getenv('DATABASE_PORT')

connection_string = f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}"
engine = create_engine(connection_string, echo=False)