import sys
import random
import chromadb
from sqlalchemy import select, and_, func
from db_utils.azure_db import get_session
from db_utils.user import User, Watched, Rating, RecommendationsHistory
from db_utils.movie import Movie
from main import get_movie_history_and_ratings, generate_candidates, get_recommendations
import datetime
import numpy as np
import json

# Initialize database session

# # stmt = select(Watched.movie_id, Rating.rating).\
# #         outerjoin(Rating, and_(Watched.user_id == Rating.user_id, Watched.movie_id == Rating.movie_id)).\
# #         where(Watched.user_id == 1).where(Watched.date_added <= ).order_by(Watched.date_added)
# stmt = select(RecommendationsHistory.recommendations).\
#     where(RecommendationsHistory.user_id == 1)

# result = session.execute(stmt)

# for row in result:
    
#     print(row)

session = get_session()

def detect_feedback_loops(session, threshold=0.7):
    # Query to fetch all recommendations
    query = select(RecommendationsHistory.recommendations)
    results = session.execute(query).fetchall()

    # Flatten the lists and count occurrences of each movie
    movie_recommendation_counts = {}
    for movie_list in results:
        if movie_list[0]:
            # print(result)
            # print(result[0])
            # print(movie_list)
            # print(movie_list[0])
            
            movie_titles = movie_list[0].split(',')

            for movie_id in movie_titles:
                # print(movie_id)
                movie_recommendation_counts[movie_id] = movie_recommendation_counts.get(movie_id, 0) + 1
        

    # Find the maximum number of recommendations for a single movie
    max_recommendations = max(movie_recommendation_counts.values(), default=0)

    # Identify movies that are recommended too often
    feedback_loops_detected = []
    for movie_id, count in movie_recommendation_counts.items():
        if count > threshold * max_recommendations:
            # print(count)
            feedback_loops_detected.append(movie_id)

    return feedback_loops_detected

# Setting a threshold for feedback loop detection
threshold = 0.7

# Detect feedback loops
feedback_loops = detect_feedback_loops(session, threshold)
if feedback_loops:
    print("Feedback loops detected in the following movies:")
    for movie_id in feedback_loops:
        print(f"Movie ID: {movie_id}")
else:
    print("No significant feedback loops detected.")

# Close the session
session.close()