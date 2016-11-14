#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


SCHEMA = """
CREATE TABLE IF NOT EXISTS source_matrix(
    hash TEXT PRIMARY KEY,
    np_array BLOB NOT NULL,     -- the numpy array, as a blob.
    n_tokens INTEGER NOT NULL   -- the amount of tokens, (excluding start/end)
);
"""

import io
import sqlite3

import io
import numpy as np

from vectorize_tokens import vectorize_tokens
from vocabulary import vocabulary


assert len(vocabulary) < 256


class CondensedCorpus:
    """
    Represents a corpus with condensed tokens according to a vocabulary.

    Can get results by rowid (ONE-INDEXED!) or by file SHA 256 hash.

    >>> from corpus import Token
    >>> c = CondensedCorpus.connect_to(':memory:')
    >>> tokens = (Token(value='var', type='Keyword', loc=None),)
    >>> c.insert('123abc', tokens)
    >>> x, y, z = c['123abc']
    >>> x, y, z
    (0, 86, 99)
    >>> file_hash, rtokens = c[1]
    >>> file_hash
    '123abc'
    >>> x, y, z = rtokens
    >>> x, y, z
    (0, 86, 99)
    """

    def __init__(self, conn):
        conn.executescript(SCHEMA)
        conn.commit()
        self.conn = conn

    @classmethod
    def connect_to(cls, filename):
        conn = sqlite3.connect(filename)
        return cls(conn)

    def get_tokens_by_hash(self, file_hash):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT np_array FROM source_matrix
            WHERE hash = ?
        """, (file_hash,))
        blob, = cur.fetchone()
        return unblob(blob)

    def get_result_by_rowid(self, rowid):
        assert isinstance(rowid, int)
        cur = self.conn.cursor()
        cur.execute("""
            SELECT hash, np_array FROM source_matrix
            WHERE rowid = ?
        """, (rowid,))
        file_hash, blob = cur.fetchone()
        return file_hash, unblob(blob)

    def __getitem__(self, key):
        if isinstance(key, (str, bytes)):
            return self.get_tokens_by_hash(key)
        else:
            return self.get_result_by_rowid(key)

    def insert(self, hash_, tokens):
        dimensions = 2 + len(tokens)
        array = np.empty(dimensions, dtype=np.uint8)

        for t, index in enumerate(vectorize_tokens(tokens)):
            array[t] = index

        filelike = io.BytesIO()
        np.save(filelike, array)

        self.conn.execute("""
            INSERT INTO source_matrix(hash, np_array, n_tokens)
                 VALUES (?, ?, ?)
         """, (hash_, filelike.getbuffer(), len(tokens)))
        self.conn.commit()


def unblob(blob):
    assert isinstance(blob, bytes)
    with io.BytesIO(blob) as filelike:
        return np.load(filelike)