import requests
from typing import Optional
from sqlalchemy import String, Integer, Float, Date, Table, Column, ForeignKey, select
from db_utils.azure_db import Base, get_session
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import warnings

association_table = Table(
    "association_table",
    Base.metadata,
    Column("movie_id", ForeignKey("Movies.movie_id")),
    Column("right_id", ForeignKey("MovieGenres.genre_id")),
)

class Genre(Base):
   __tablename__ = "Genres"
   
   genre_id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
   genre : Mapped[str] = mapped_column(String, primary_key=True)
   #TODO make sure genres don't get added twice

   def commit_genre(genre : str):
      session = get_session()
      with session:
          genre = Genre(genre)
          session.add(genre)
          session.commit()

   def __init__(self, genre : dict):
      super().__init__(genre_id=genre['id'], genre=genre['name']) #wow much code such naming 

class MovieGenres(Base):
   __tablename__ = "MovieGenres"
   
   genre_id : Mapped[int] = mapped_column(String, primary_key=True)
   movie_id : Mapped[str] = mapped_column(String, primary_key=True)

class Movie(Base):
   __tablename__ = "Movies"

   movie_id : Mapped[str] =  mapped_column(String, primary_key=True, autoincrement=False, nullable=False)
   title : Mapped[Optional[str]] = mapped_column(String)
   imdb_id : Mapped[Optional[str]] = mapped_column(String)
   tmdb_id : Mapped[Optional[int]]= mapped_column(Integer)
   original_title : Mapped[Optional[str]] = mapped_column(String)
   adult : Mapped[Optional[str]] = mapped_column(String)
   belongs_to_collection : Mapped[Optional[str]] = mapped_column(String)
   poster_path : Mapped[Optional[str]] = mapped_column(String)
   budget : Mapped[Optional[int]] = mapped_column(Integer)
   homepage : Mapped[Optional[str]] = mapped_column(String)
   original_language : Mapped[Optional[str]] = mapped_column(String)
   overview : Mapped[Optional[str]] = mapped_column(String)
   popularity : Mapped[Optional[float]] = mapped_column(Float)
   production_companies : Mapped[Optional[str]] = mapped_column(String)
   production_countries : Mapped[Optional[str]] = mapped_column(String)
   release_date : Mapped[Optional[datetime.date]] = mapped_column(Date)
   spoken_languages : Mapped[Optional[str]] = mapped_column(String)
   status : Mapped[Optional[str]] = mapped_column(String)
   vote_average : Mapped[Optional[float]]
   vote_count : Mapped[Optional[int]] = mapped_column(Integer)
    
   def _get_movie_info(self, override_id=None):
      required_keys = ["tmdb_id", "imdb_id", "title", "original_title", "adult", "belongs_to_collection", 
                       "poster_path", "budget", "genres", "homepage", "original_language", "overview", 
                       "popularity", "production_companies", "production_countries", "release_date", "spoken_languages",
                       "status", "vote_average", "vote_count"]
      return_dict = {}
      if override_id != None:
         r = requests.get(f'http://api_url:8080/movie/{override_id}', timeout=10)
      else:
         r = requests.get(f'http://api_url:8080/movie/{self.id}', timeout=10)

      if r.status_code == 400:

        for key in required_keys:
          return_dict[key] = None
        
        return_dict.pop('genres')
        return return_dict

      else:
        response = r.json()

        for key in required_keys:
         try:
            return_dict[key] = response[key]
            if key == "release_date" and key is not None:
               return_dict[key] = datetime.strptime(return_dict[key], '%Y-%m-%d') #TODO check if string format is correct
            #elif key == "genres":
             # for genre in return_dict[key]:
                 # try:
                 # Genre.commit_genre(genre) #keep track of genres separately from movie table
                  #except:
                     #print(f'Error committing genre {genre}, perhaps it already exists?')
         except:
           return_dict[key] = None

      return_dict.pop("genres") #TODO get info about genres back
      return_dict.pop("production_companies")
      return_dict.pop("production_countries")
      return_dict.pop("spoken_languages")
      return_dict.pop("belongs_to_collection")
      #return_dict.pop("overview")
      return return_dict 

   @classmethod
   def exists_in_db(cls, id):
      with get_session() as session:
         q = select(Movie).where(Movie.movie_id==id)
         result = session.scalars(q)
         movie_exists = len(result.all()) != 0
         if movie_exists:
            warnings.warn("Warning...Attempting to create a Movie object which already exists in the db. Creation cancelled")
            return True
         else:
            return False

   def __init__(self, id):
      self.id = id
      
      # Since we don't need to store the movie details in real time, we can just store IDs and handle that at some later point
      # if self.id == "-1":
      #    #creating test movie for unittesting
      #    return_dict = self._get_movie_info(override_id='get+shorty+1995')
      # else:
      #    return_dict = self._get_movie_info()
      super().__init__(movie_id=id)
      #insert into chroma db


if __name__ == '__main__':
   session = get_session()
   with session:
    movie =  Movie('pirates+1986')
    #TODO duplicate key errors.

    session.add(movie)
    session.commit()

