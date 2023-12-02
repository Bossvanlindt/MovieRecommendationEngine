import sys
import random
from sqlalchemy import select, and_, func, desc
from db_utils.azure_db import get_session
from db_utils.user import User, Watched, Rating, UserModelMap
from db_utils.movie import Movie
from main import get_movie_history_and_ratings, generate_candidates, get_recommendations
import datetime
import random
import numpy as np
import os
import argparse
import requests
import subprocess


parser = argparse.ArgumentParser()
session =  get_session()

parser.add_argument("container_name") # container_name = "main" or "nightly"
args = parser.parse_args()

# date_format = '%Y-%m-%d %H:%M'
# date_format = '%Y-%m-%d'
# t1 = '2023-11-22'
# t2 = '2023-11-23'

time_lag = 12

t2 = datetime.datetime.utcnow()
t1 = t2 - datetime.timedelta(hours = time_lag)

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

    return movies, ratings

def eval(user_list, url = None):
    valid_count = 0

    new_movie_ratings_dict = {}
    for r in ratings:
        new_movie_ratings_dict[r] = 0
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
            # recs = requests.get(url+"/recommend/" + str(user_id)).content.decode()
            # recommendations = recs.split(",")
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

    # print("Number of valid users = " + str(valid_count)) # number of users with changed histories given timestamps t1 and t2
    # print("New Movie Counts Per Valid User = ", new_movie_count_list)
    # print("Total Comparisons Per Valid User = ", total_comparisons_list)

    new_movie_comparisons_ratio = [i/j for i,j in zip(new_movie_count_list, total_comparisons_list)]

    # print("Ratio Per Valid User = ", new_movie_comparisons_ratio)
    average_ratio = np.array(new_movie_comparisons_ratio).mean()
    # print("Average Ratio = ", average_ratio)
    # print("New Movie Ratings Aggregated:")
    # print(new_movie_ratings_dict)

    sum_ratings = 0
    num_ratings = 0
    for r in ratings:
        sum_ratings += new_movie_ratings_dict[r]*r
        num_ratings += new_movie_ratings_dict[r]
    mean_ratings = sum_ratings/num_ratings

    print(average_ratio)
    # print(mean_ratings)
    # return average_ratio, mean_ratings
    # return average_ratio

num_sampled_users = 10000
# stmt = select(Watched.user_id).order_by(func.random())
# stmt = select(Watched.user_id).distinct(Watched.movie_id).order_by(Watched.date_added)
# user_list = session.scalars(stmt).all()[:num_sampled_users]

# main_url = os.environ.get("MAINURL")
# nightly_url = os.environ.get("NIGHTLYURL")

# bashCommandName = 'echo -n $NAME'
# container_name = subprocess.check_output(['bash','-c', bashCommandName])

'''
https://stackoverflow.com/questions/51544433/python-getting-docker-container-name-from-the-inside-of-a-docker-container
'''

stmt = select(UserModelMap.user_id).where(UserModelMap.model_version == args.container_name).order_by(func.random())
user_list = session.scalars(stmt).all()

if len(user_list) > num_sampled_users:
    user_list = user_list[:num_sampled_users]
# print(len(user_list))

if __name__ == "__main__":
    eval(user_list)
