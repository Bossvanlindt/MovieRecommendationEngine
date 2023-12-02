from confluent_kafka import Consumer
import time
from db_utils.azure_db import get_session
from db_utils.user import User, Watched, Rating
from db_utils.movie import Movie
import random

KAFKA_URL = ''
config = {'bootstrap.servers': KAFKA_URL,
          'group.id': f'group_{random.randint(0,10000)}',
          'enable.auto.commit': 'true',
          'auto.offset.reset': 'latest'}

consumer = Consumer(config)
topic = 'movielog5'

def consume_loop(consumer, topic):
    with get_session() as session:
        try:
            consumer.subscribe([topic])
            count = 0
            start = time.time()
            while True:
                msg = consumer.poll(timeout = 5.0)
                msg = msg.value().decode()
                parse_line(msg, session) # decode from byte to string
                count += 1

                # Commit to database only every 10000 messages to avoid overhead
                if count % 10000 == 0:
                    time_taken = time.time() - start
                    print(f'Consumed {count} messages in {time_taken} seconds ==> {count/time_taken} messages per second')
                    session.commit()
        finally:
            # closing the consumer would "commit" our final offset if the corresponding flag 'enable.auto.commit' was true (i think?)
            consumer.close()
    
def parse_line(line, session):
    line_tokens = line.split(',')
    if len(line_tokens[0].split('T')) > 2: # extra 'T' in time-stamp -- this is a very ugly way to handle it, should refactor this if possible
        pass
    else:
        date, time = line_tokens[0].split('T')
        user_id = line_tokens[1]
        command_tokens = line_tokens[2].split('/')
        if len(command_tokens) == 1 or user_id.isnumeric() == False:
            pass
        else:
            request_type = command_tokens[1]
    
            if request_type == 'data':
                movie_id = command_tokens[3]
                watched = Watched(user_id=user_id, movie_id=movie_id)
                if watched != None:
                    # print(f'Adding Watched: {user_id}:{movie_id}:{movie_minute}')
                    session.merge(watched)

            elif request_type == 'rate':
                movie_id, rating = command_tokens[2].replace('\n', '').split('=')

                if rating.isnumeric():
                    rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
                    session.merge(rating)

            else:
                pass

consume_loop(consumer, topic)

if __name__ == '__main__':
    parse_line('2023-10-25T00:56:34,185706,GET /data/m/the+dark+knight+2008/35.mpg', get_session())