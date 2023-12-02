import sqlalchemy as db
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import Session, DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

class Base(DeclarativeBase):
    pass

# As host, we use the hostname of the database container so it can connect to it
def get_session():
    connection_url = URL.create(
        "postgresql",
        username="postgres",
        password="PASSWORD",
        host=os.environ.get("DATABASE_HOST"),
        port=5432,
        database="postgres"
    )
    
    engine = db.create_engine(connection_url)
    return Session(engine, autoflush=False)


