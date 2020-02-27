import os
import sqlite3
from flask import g

def connect_db():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sql = sqlite3.connect('{}/dbase/food_log.db'.format(dir_path))
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    if not hasattr(g, 'sqlite3_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db