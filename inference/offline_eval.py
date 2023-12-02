import sys
import random
import chromadb
from sqlalchemy import select, and_, func
from db_utils.azure_db import get_session
from db_utils.user import User, Watched, Rating
from db_utils.movie import Movie
from main import get_movie_history_and_ratings, generate_candidates, get_recommendations
import datetime
import numpy as np


session = get_session()

# Set the time lag for evaluation
time_lag = 10

# Calculate the time range for evaluation
t2 = datetime.datetime.utcnow()
t1 = t2 - datetime.timedelta(days=time_lag)

ratings = [1, 2, 3, 4, 5]

def get_movie_history_and_ratings_timestamped(user_id, t):
    stmt = select(Watched.movie_id, Rating.rating).\
        outerjoin(Rating, and_(Watched.user_id == Rating.user_id, Watched.movie_id == Rating.movie_id)).\
        where(Watched.user_id == user_id).where(Watched.date_added <= t).order_by(Watched.date_added)
    result = session.execute(stmt)

    movies, ratings = [], []
    for movie_id, rating in result:
        movies.append(movie_id)
        ratings.append(rating if rating is not None else 3)

    # print(movies)
    # print(ratings)

    return movies, ratings

def eval(user_list):
    valid_count = 0
    new_movie_ratings_dict = {r: 0 for r in ratings}
    new_movie_count_list = []
    total_comparisons_list = []

    for user_id in user_list:
        movie_history_t1, ratings_t1 = get_movie_history_and_ratings_timestamped(user_id, t1)
        movie_history_t2, ratings_t2 = get_movie_history_and_ratings_timestamped(user_id, t2)
        
        if movie_history_t1 == movie_history_t2:
            continue
        else:
            valid_count += 1
            # print("Valid user!")
            new_movie_count = 0
            total_comparisons = 0

            recommendations = generate_candidates(movie_history_t1, ratings_t1)
            if movie_history_t2[len(movie_history_t1)] in recommendations:
                new_movie_count += 1
                new_movie_ratings_dict[ratings_t2[len(movie_history_t1)]] += 1
            total_comparisons += 1

            new_movies = movie_history_t2[len(movie_history_t1):]
            new_ratings = ratings_t2[len(ratings_t1):]

            for i, m in enumerate(new_movies[:-1]):
                movie_history_t1.append(m)
                ratings_t1.append(new_ratings[i])
                recommendations = generate_candidates(movie_history_t1, ratings_t1)
                if movie_history_t2[len(movie_history_t1)] in recommendations:
                    new_movie_count += 1
                    new_movie_ratings_dict[ratings_t2[len(movie_history_t1)]] += 1
                total_comparisons += 1


            new_movie_count_list.append(new_movie_count)
            total_comparisons_list.append(total_comparisons)

    if valid_count == 0:
        print("No valid users sampled -- try again? :p ")
        return None

    new_movie_comparisons_ratio = [i / j for i, j in zip(new_movie_count_list, total_comparisons_list)]
    average_ratio = np.array(new_movie_comparisons_ratio).mean()
    sum_ratings = sum(new_movie_ratings_dict[r] * r for r in ratings)
    num_ratings = sum(new_movie_ratings_dict.values())
    mean_ratings = sum_ratings / num_ratings if num_ratings else 0

    if mean_ratings > 0 and average_ratio > 0:
        return True
    else: return False

    # print(average_ratio)
    # print(mean_ratings)

num_sampled_users = 20000
stmt = select(Watched.user_id).order_by(func.random())
user_list = session.scalars(stmt).all()[:num_sampled_users]

if __name__ == "__main__":
    eval(user_list)
