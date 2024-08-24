## **Description**

---

This is the backend for the Cover Letter Generation  Chrome Extension. We’re utilising the bert-base-uncased embedding model to generate embeddings and Postgres combined with it’s pgvector extension to store and index the vectors. The database scheme is two tables. One for users with the columns: id, email, password and name. Along with a second table hosting all the cvs consisting of 3 columns: id, cv_lines, embedding with an IVFFLAT index based on the cosine algorithm for the embeddings.

This directory then serves as the backend for cv-extension-fe

## Prerequisites

---

- Python 3.12.5 was used for development
- To actually generate the embeddings pytorch was utilised and thus you need C++ Redistributable. Easiest way to get it is to download Visual Studio and select windows desktop app development. Torch is tricky to download for some people but if you do have
- PSQL SQL Shell 2022 minimum for interacting with the database

## **Installation**

---

All the necessary packages can be found within the requirements.txt file. There’s also a Utility class for DB interactions and all features. Be sure to setup an .env file containing: 

```python
DB_HOST=localhost # (hosted location)
DB_USER=postgres # (username for your DB login)
DB_PASSWORD=password # (password for DB_USER)
DB_PORT=5432 # (this is the standard port number for PSQL, if you changed then use yours)

EMBEDDING_MODEL_NAME=model_name # (I used 'bert-base-uncased')

GEMINI_API_KEY=key # (This is for generating the cover letter response. Feel Free to use whatever model you want)
```

Remember to make a gitignore file that ignores **.env

## **Contact**

---

- Email: jadorethompson6@gmail.com
- Discord: zenzjt
