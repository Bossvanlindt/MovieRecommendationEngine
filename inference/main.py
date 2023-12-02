import sys
import os
import json
import pandas as pd
import numpy as np
import requests
import pickle
from pathlib import Path

from flask import Flask, request, Response
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
import chromadb
from db_utils.azure_db import get_session
from db_utils.user import User, Watched, Rating
from sqlalchemy import select, func, cast, Numeric, and_

# Create the API
app = Flask(__name__)
CORS(app)


# Prometheus metrics
metrics = PrometheusMetrics(app)


# Connect to ChromaDB and Azure DB
client = chromadb.PersistentClient(path="./chromadb_23k")
movies_collection = client.get_or_create_collection(name="movies", metadata={"hnsw:space": "cosine"})
session = get_session()

script_path = Path(__file__, '..').resolve()
# Constants: popularities dictionary and top 20 movies
with open(script_path.joinpath("pop_dict.pkl"), "rb") as f:
    popularities = pickle.load(f)
top_20 = [
    "big+hero+6+2014",
    "avatar+2009",
    "john+wick+2014",
    "gone+girl+2014",
    "the+hunger+games+mockingjay+-+part+1+2014",
    "pulp+fiction+1994",
    "the+dark+knight+2008",
    "blade+runner+1982",
    "the+avengers+2012",
    "the+maze+runner+2014",
    "dawn+of+the+planet+of+the+apes+2014",
    "whiplash+2014",
    "fight+club+1999",
    "guardians+of+the+galaxy+2014",
    "the+shawshank+redemption+1994",
    "forrest+gump+1994",
    "pirates+of+the+caribbean+the+curse+of+the+black+pearl+2003",
    "star+wars+1977",
    "schindlers+list+1993",
    "rise+of+the+planet+of+the+apes+2011",
]


# Get user watch history and ratings. Default rating if not rated is 3.
# Returns a list of tuples (movie_id, rating)
def get_movie_history_and_ratings(user_id):
    # Verify that the user_id is numeric
    if not user_id.isnumeric():
        return [], []

    # Retrieve the user's watch history along with their ratings for each movie
    stmt = select(Watched.movie_id, Rating.rating).\
        outerjoin(Rating, and_(Watched.user_id == Rating.user_id, Watched.movie_id == Rating.movie_id)).\
        where(Watched.user_id == user_id)
    result = session.execute(stmt)

    movies, ratings = [], []
    for movie_id, rating in result:
        movies.append(movie_id)
        ratings.append(rating if rating is not None else 3)

    return movies, ratings


# Generate 20 sorted movie recommendations given a user's movie history and ratings
# High-level logic: for each movie in the user's history, get the top 20 most similar movies with the vector database.
# All these movies are ranked according to a function of similarity, popularity, and the rating of the original movie.
def generate_candidates(movies, ratings, max_num_movies=20, num_candidates_per_movie=20):
    # Keep only movies that are in our vector database and have a rating > 2
    filtered_movies = []
    for movie, rating in zip(movies, ratings):
        if len(movies_collection.get(ids=[movie])["ids"]) != 0 and rating > 2:
            filtered_movies.append(movie)

    # Return default the default recommendation if we can't provide a personalized one yet
    if len(filtered_movies) == 0:
        return top_20

    # TODO: filter out R-rated movies for non-adult users

    # Get num_candidates_per_movie potential candidates per movie by querying the vector database
    movie_embeddings = movies_collection.get(filtered_movies, include=["embeddings"])["embeddings"]
    candidates = movies_collection.query(query_embeddings=movie_embeddings, n_results=num_candidates_per_movie)["ids"]

    # Return sorted candiddates 
    return select_and_sort_candidates(movies, ratings, candidates, filtered_movies, max_num_movies)


def select_and_sort_candidates(movies, ratings, candidates, filtered_movies, max_num_movies=20):
    # Create a dictionary to store candidate scores by adding the ratings of the movies they are derived from
    candidate_scores = {}
    for i, candidate_list in enumerate(candidates):
        # Get the rating of the original movie
        rating = ratings[movies.index(filtered_movies[i])]
        for candidate in candidate_list:
            if candidate not in movies:
                # Use a default popularity of 1e-4 if not found to prevent any movie from having score = 0
                popularity = popularities.get(candidate, 1e-4)
                # Increase the candidate's score by the rating of the original movie and its popularity
                candidate_scores[candidate] = candidate_scores.get(candidate, 0) + rating * popularity

    # Get the top n candidates based on score
    sorted_scores = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
    top_candidates = [movie for movie, _ in sorted_scores[:max_num_movies]]
    return top_candidates

@app.route("/recommend/<user_id>", methods=["GET"])
def get_recommendations(user_id):
    try:
        movies, ratings = get_movie_history_and_ratings(user_id)
        recommendations = generate_candidates(movies, ratings)
        # recommendations = top_20
        return Response(",".join(recommendations), mimetype="text/html"), 200
    except Exception as e:
        app.logger.error("Exception during execution of get_recommendations: %s", e) 
        return Response("Exception during execution", mimetype="text/html"), 500



# Endpoint to see user watch history
@app.route("/watched/<user_id>", methods=["GET"])
def get_watched_movies(user_id):
    try:
        stmt = select(Watched.movie_id).where(Watched.user_id == user_id)
        watched_movies = session.scalars(stmt).all()
        # Manually increment 200 status code metric
        return Response(",".join(watched_movies), mimetype="text/html"), 200
    except IndexError as e:
        # Manually increment 404 status code metric
        app.logger.error("Index Error during execution of get_watched_movies: %s", e)
        return Response("User not found", mimetype="text/html"), 404


# This is used for testing the API locally
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8087)
