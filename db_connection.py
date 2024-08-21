import os
from dotenv import load_dotenv

import psycopg2
from psycopg2 import pool


load_dotenv('.env')
conn_params = {
    "host": os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'dbname': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT')
}

conn_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **conn_params)


def get_db_connection():
    conn = conn_pool.getconn()
    try:
        yield conn
    finally:
        conn_pool.putconn(conn)
