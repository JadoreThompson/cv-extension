import os
from dotenv import load_dotenv

import psycopg2
from psycopg2 import pool

from contextlib import contextmanager


load_dotenv('.env')
conn_params = {
    "host": os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'dbname': os.getenv('DB_NAME'),
    'port': os.getenv('DB_PORT')
}

conn_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **conn_params)


@contextmanager
def get_db_connection():
    conn = conn_pool.getconn()
    yield conn


def return_conn(conn):
    conn_pool.putconn(conn)
