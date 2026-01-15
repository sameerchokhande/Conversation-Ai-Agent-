import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root@123",
        database="dentaldb"
    )


def get_db():
    """Backward-compatible alias for get_db_connection().

    Existing code imports `get_db` from this module, so provide a thin
    wrapper to avoid changing callers.
    """
    return get_db_connection()
