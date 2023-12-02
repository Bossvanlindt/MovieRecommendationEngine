import unittest

from sqlalchemy import select, delete
from db_utils.azure_db import get_session
from db_utils.movie import Movie
from db_utils.user import User
class MovieObjectTestCase(unittest.TestCase):
    session = get_session()

    def tearDown(self):
        stmt = delete(Movie).where(Movie.movie_id=='-1')
        self.session.execute(stmt)
        self.session.flush()
        self.session.commit()

    def test_object_created(self):
       #test that a movie was created and added to the database.  
        with self.session as session:
            movie =  Movie('-1')
            session.merge(movie)
            session.commit()
        
            test_movie = session.get(Movie, '-1')
            self.assertEqual(test_movie.movie_id, '-1')
            
    def test_api_call(self):
        movie_dict = Movie("-1")._get_movie_info(override_id='get+shorty+1995')
        self.assertEqual(movie_dict['title'], 'Get Shorty')
    
    def test_object_exists(self):
        with self.session as session:
            movie = Movie("-1")
            session.merge(movie)
            session.commit()

            with self.assertWarns(Warning):
                Movie.exists_in_db('-1')
                

class UserObjectTestCase(unittest.TestCase):
    session = get_session()

    def tearDown(self):
        stmt = delete(User).where(User.user_id == -1)
        self.session.execute(stmt)
        self.session.flush()
        self.session.commit()

    def test_object_created(self):
       #test that a user was created and added to the database.  
        with self.session as session:
            user =  User(-1)
            session.add(user)
            session.commit()
        
            stmt = select(User).where(User.user_id == '-1')
            test_user = session.scalars(stmt).first()
            self.assertEqual(test_user.user_id, -1)
            
    def test_api_call(self):
        test_user = User(-1)
        age, occupation, gender = test_user._get_user_info(override_id=1)
        self.assertEqual((age, occupation, gender), (34, 'sales/marketing', 'M'))
    
    def test_object_exists(self):
        with self.session as session:
            user = User(-1)
            session.add(user)
            session.commit()
            
            with self.assertWarns(Warning):
                User.exists_in_db(-1)
    

if __name__ == '__main__':
    unittest.main()

#Tests:
#parsing values. 
#Data quality tests.