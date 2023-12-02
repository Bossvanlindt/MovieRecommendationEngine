# Movie Recommendation Engine
*Yann Bonzom, Sep-Dec 2023*

*Note*: This project was done for a course in collaboration with 4 colleagues.

## Overview
For this semester project, we built a movie recommendation engine to power a simulated Netflix-style streaming platform serving 27K movies to 1M simulated users. The overall setup is as follows: 
- The Postgres database container stores user behaviour such as movies watched and reviews
    - The [db_utils](./db_utils/) package enables communication with this database via SQLAlchemy and is installed via `pip install -e .`
- The [data_parsing](./data_parsing/) container continuously processes every line from the Kafka stream to save user watch and rating histories to the database
- The [load_balancer](./load_balancer/) container serves as our Flask load balancer to handle Canary Release logic in case of model updates. The directory also contains Python scripts to handle the deployment logic between main and nightly/canary inference container versions, scheduling an online evaluation 12h after the nightly's deployment to compare the two services and replace them accordingly. 
- The [inference](./inference/) contains the Flask API with the model logic to provide inferences. Essentially, it uses the ChromaDB vector database (which is set up using a static movie catalog in the [vectordb_scripts](./vectordb_scripts/) directory) to generate 20 candidates (i.e., similar movies) per movie a user has seen. We then sort those candidates by a mix of popularity and ratings given to provide our final set of 20 movie recommendations. 
- The [monitoring](./monitoring/) setup uses Grafana and Prometheus to serve a dashboard on port 3000 to monitor system performance, and automatically sends messages in our Slack channel in case of issues
- The [tests](./tests/) directory contains unit tests for our services
- Finally, the [reports](./reports/) directory contains our reports submitted for each of the 3 project milestones. They include reflections on our setup, system performance reviews, and reflections on our team work and individual contributions. 

## ML Recommendation Logic
In the [vectordb_scripts](./vectordb_scripts/) directory, we initialize a vector database with our movie catalog. This works by calculating sentence embeddings with the open-source **all-MiniLM-L6-v2** model, though other embedding models such as OpenAI's **text-embedding-ada-002** can also be used for potentially improved embedding quality. 

When the inference service receives a request for recommendations for a given user, we (1) retrieve the user's watch history from the database, (2) retrieve the 20 most similar movies for each movie they've seen using ChromaDB's built-in Approximate Nearest Neighbour (ANN) implementation, and (3) sort these based on user ratings and movie popularity scores to return our top 20 picks.

## CI/CD & Canary Release Logic
The project was initially developed using GitLab CI/CD, so all our CI/CD logic is in the [.gitlab-ci.yml](.gitlab-ci.yml) file. It works based on the tag of a commit to deploy the main inference container, Kafka reader, and nightly/canary release inference container accordingly. It uses a CI/CD runner on our local server to perform these actions in an isolated environment. 

The canary release works as follows: if a commit is tagged with *release-recommender-nightly-*, we (1) run an offline evaluation on the new model logic, and if it passes, (2) build the nightly image to push it to Dockerhub, and (3) execute the [deploy_inference_container.py](./load_balancer/deploy_inference_container.py) script which will launch the nightly container, schedule the online evaluation to take place in 12h via a cronjob, and perform the main inference container replacement logic if the new version outperforms the old one. For model versioning, the appropriately-tagged containers remain saved on Dockerhub for us to work with. 

## Postgres Database Container
To start this container, run `docker run --name database -e POSTGRES_PASSWORD="PASSWORD" -d --mount source=postgres_database,target=/var/lib/postgresql/data  --network=monitoring-network -p 5432:5432 postgres`. This stores all data to a volume to make it persist, and uses the monitoring network to allow all containers to communicate with the database. Please see [db_utils](./db_utils/) for details on table names and schemas. 