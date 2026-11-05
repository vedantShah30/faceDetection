
import sqlite3
import pandas as pd

from config import DATABASE_PATH


def get_connection():

    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def fetch_one(query, params=()):

    with get_connection() as conn:
        return conn.execute(
            query, params
        ).fetchone()


def fetch_all(query, params=()):

    with get_connection() as conn:
        return conn.execute(
            query, params
        ).fetchall()


def fetch_dataframe(query, params=()):

    with get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )
