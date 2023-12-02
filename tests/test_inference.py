import unittest
from unittest.mock import patch
from sqlalchemy import select, delete
import sys
from flask import Response
from os import path
# Path is required to import main's functions. Specific to the Docker container environment of the CI/CD runner. 
sys.path.append('/builds/comp585_2023f/team-5/./inference')
from main import (
    get_recommendations, 
    get_watched_movies,
    get_movie_history_and_ratings, 
    generate_candidates,
    select_and_sort_candidates,
    top_20
)

class APIEndpointTestCase(unittest.TestCase):
    # Test API endpoint to get recommendations for a given user
    def test_get_recommendations(self):
        # Mock both get_movie_history_and_ratings and generate_candidates to verify output format
        with patch('main.get_movie_history_and_ratings') as mock_get_movie_history_and_ratings:
            with patch('main.generate_candidates') as mock_generate_candidates:
                mock_get_movie_history_and_ratings.return_value = (['movie1', 'movie2', 'movie3'], [3, 4, 5])
                mock_generate_candidates.return_value = ['movie4', 'movie5', 'movie6']
                response, status_code = get_recommendations('1')
                self.assertEqual(status_code, 200)
                self.assertEqual(response.data.decode('utf-8'), 'movie4,movie5,movie6')

class RecommendationLogicTestCase(unittest.TestCase):
    # Test logic for setting the average rating if no rating is provided
    def test_get_movie_history_and_ratings(self):
        # Mock the database call to return a list of movie ids and ratings
        with patch('main.session.execute') as mock_execute:
            mock_execute.return_value = [('movie1', None), ('movie2', 4), ('movie3', 5)]
            movies, ratings = get_movie_history_and_ratings('1')  # user_id doesn't matter as we give a default list of movies
            self.assertEqual(movies, ['movie1', 'movie2', 'movie3'])
            self.assertEqual(ratings, [3, 4, 5])

    # Tests if sorting works correctly for the 2 movies' candidates
    def test_select_and_sort_candidates(self):
        candidates = [['toy+story+1995', 'toy+story+2+1999', 'toy+story+3+2010', 'small+fry+2011', 'hawaiian+vacation+2011', 'it+runs+in+the+family+2003', 'clifford+1994', 'for+the+birds+2000', 'tmnt+2007', 'partysaurus+rex+2012', 'heartbeeps+1981', 'a+goofy+movie+1995', 'the+gnome-mobile+1967', 'the+master+of+disguise+2002', 'rocket+gibraltar+1988', 'jingle+all+the+way+2+2014', 'wide+awake+1998', 'drop+dead+fred+1991', 'across+the+sea+of+time+1995', 'uncle+nino+2003'], ['jumanji+1995', 'the+spiderwick+chronicles+2008', 'peter+pan+2003', 'the+last+mimzy+2007', 'little+monsters+1989', 'the+borrowers+2011', 'the+wizard+of+oz+1939', 'dinotopia+2002', 'tom+thumb+1958', 'the+new+adventures+of+pippi+longstocking+1988', 'the+indian+in+the+cupboard+1995', 'mighty+joe+young+1998', 'ice+age+2002', 'journey+to+the+center+of+the+earth+2008', 'inkheart+2008', 'peter+pan+1953', 'true+heart+1999', 'the+little+engine+that+could+1991', 'the+jungle+book+2+2003', 'alice+in+wonderland+2010']]
        movies = ['toy+story+1995', 'jumanji+1995']
        sorted_candidates = select_and_sort_candidates(movies, [4, 5], candidates, movies)
        expected_candidates = ['the+wizard+of+oz+1939', 'ice+age+2002', 'alice+in+wonderland+2010', 'peter+pan+1953', 'toy+story+2+1999', 'toy+story+3+2010', 'inkheart+2008', 'the+spiderwick+chronicles+2008', 'the+indian+in+the+cupboard+1995', 'the+jungle+book+2+2003', 'journey+to+the+center+of+the+earth+2008', 'tmnt+2007', 'hawaiian+vacation+2011', 'peter+pan+2003', 'for+the+birds+2000', 'a+goofy+movie+1995', 'small+fry+2011', 'dinotopia+2002', 'mighty+joe+young+1998', 'drop+dead+fred+1991']
        self.assertEqual(sorted_candidates, expected_candidates)

    # TODO: write tests with the ChromaDB directly. Will have to figure out how to work with its path properly in the test environment

if __name__ == '__main__':
    unittest.main()
