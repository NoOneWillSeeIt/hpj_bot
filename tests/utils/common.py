from copy import copy
import sqlite3
from typing import List, Self, Tuple

import aiosqlite

import db.queries as syncdb


class Tree:
    def __init__(self, name: object, children: List[Self]) -> None:
        self.name = name
        self.children = children

    @property
    def key(self):
        return self.name

    @property
    def is_last_node(self):
        return self.children == []

    def search_loops(self, prev_nodes: list = []) -> list:
        prev_nodes.append(self.name)

        if self.name in prev_nodes[:-1]:
            return prev_nodes

        result = []
        for child in self.children:
            child_res = child.search_loops(copy(prev_nodes))
            if child_res:
                result.append(child_res)

        return result

    def search_unique_nodes(self, nodes: set = set()):
        nodes.add(self.name)
        for child in self.children:
            child.search_unique_nodes(nodes)

        return nodes


def recursion_limiter(limit: int = -1):

    def deco(func):
        func.limit = limit

        def wrapper(*args, **kwargs):
            func.limit -= 1
            if func.limit == 0:
                raise RecursionError
            result = func(*args, **kwargs)
            func.limit += 1
            return result

        return wrapper

    return deco


async def create_test_db() -> Tuple[str, aiosqlite.Connection]:
    db_path = ':memory:'
    conn = await aiosqlite.connect(db_path)
    await conn.execute('''
            CREATE TABLE journal(chat_id BIGINT PRIMARY KEY, entries TEXT, alarm TEXT);
        ''')
    return db_path, conn


def create_test_sync_db() -> Tuple[str, sqlite3.Connection]:
    db_path = ':memory:'
    conn = sqlite3.connect(db_path)
    syncdb.create_base_table(conn)
    syncdb.create_del_tmp_table(conn)
    return db_path, conn
