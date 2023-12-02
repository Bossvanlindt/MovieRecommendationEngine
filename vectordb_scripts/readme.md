# Movie Processing

Kaggle contains more data than the provided movie catalogue (45K vs. 17K). The [create_movie_dataset.ipynb](./create_movie_dataset.ipynb) loads the Kaggle dataset, queries the course API for each movie (where ID is generated at the start), and stores the movies that are in the catalogue in [this final dataset](./kaggle_dataset/comp585_movies.csv). We also make use of the movies collected from the Kafka stream, and save these to the vector database as well.

We use ChromaDB as our vector database. It is currently stored locally and would contain all our data. [populate_chroma_with_kaggle.ipynb](./populate_chroma_with_kaggle.ipynb) contains code to create the _movies_ collection in the ChromaDB and also saves all the movies in our catalogue to it by automatically calculating embeddings and inserting them. The _movies_ collection amounts to ~223MB and this is all stored in the [inference/chromadb](../inference/chromadb/) folder.

The speed of computing these movie embeddings is very fast:

- Time to embed and save: 13:31 mins for the 17618 documents = 0.0460324668 seconds / embedding
- Roughly 0.045 seconds per query to get 10 nearest movies

Qualitatively, the results seem pretty good from the couple of tests Yann did.
