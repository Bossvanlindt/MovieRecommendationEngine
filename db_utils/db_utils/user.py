
import requests
from typing import Optional
from sqlalchemy import String, DateTime, Integer, select, Text
from db_utils.azure_db import Base, get_session
from sqlalchemy.orm import Mapped 
from sqlalchemy.orm import mapped_column 
from sqlalchemy.orm import relationship
import datetime

import warnings
class User(Base):
  #class representing a User in the system, as well as a row in the Azure database table dbo.Users

    __tablename__ = "Users"

    user_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False, nullable=False)
    age : Mapped[Optional[int]] = mapped_column(Integer)
    occupation : Mapped[Optional[str]] = mapped_column(String)
    gender : Mapped[Optional[str]] = mapped_column(String)

    @classmethod
    def exists_in_db(cls, id):
      with get_session() as session:
        q = select(User.user_id).where(User.user_id==id)
        result = session.scalars(q)
        user_exists = len(result.all()) != 0

        if user_exists:
          warnings.warn("Warning...Attempting to create a User object which already exists in the db. Creation cancelled")
          return True
        else: 
          return False

    def __init__(self, id):
      self.id=id

      # Since we don't need to store user personal data from the api in real time, we can just store IDs and handle that at some later point
      # if self.id == -1:
      #   #for testing fake users
      #   age, occupation, gender = self._get_user_info(override_id=1)
      # else:
      #   age, occupation, gender = self._get_user_info() 
      super().__init__(user_id=id)
  
    def _get_user_info(self, override_id=None):
      if override_id != None:
        r = requests.get(f'http://api_url:8080/user/{override_id}')
      else:
        r = requests.get(f'http://api_url:8080/user/{self.id}')

      if r.status_code == 400:
        age = None
        occupation = None
        gender = None
      else:
        response = r.json()
        age = response['age']
        occupation = response['occupation']
        gender = response['gender']

      return age, occupation, gender

class Rating(Base):
  __tablename__ =  "NewRatings"

  user_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
  movie_id : Mapped[str] = mapped_column(String, primary_key=True, autoincrement=False)
  rating: Mapped[int] = mapped_column(Integer)

class Watched(Base):
  __tablename__ =  "NewWatched"

  user_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
  movie_id : Mapped[str] = mapped_column(String, primary_key=True, autoincrement=False)
  date_added : Mapped[DateTime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
  
class RecommendationsHistory(Base):
    __tablename__ = "RecommendationsHistory"

    user_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    model_version : Mapped[str] = mapped_column(String)
    watch_history : Mapped[str] = mapped_column(Text)
    recommendations : Mapped[str] = mapped_column(Text)
    timestamp : Mapped[DateTime] = mapped_column(DateTime, primary_key=True, default=datetime.datetime.utcnow)

class UserModelMap(Base):
    __tablename__ = "UserModelMap"

    user_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    model_version : Mapped[str] = mapped_column(String)
    timestamp : Mapped[DateTime] = mapped_column(DateTime, primary_key=True, default=datetime.datetime.utcnow)
