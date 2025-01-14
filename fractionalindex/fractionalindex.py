from pathlib import Path
from sortedcontainers import SortedList
from fractional_indexing import generate_key_between
from fastcore.utils import *

class Indexer:
    """
    An Indexer provides insert() and friends, which generate a fractional index KEY to be used when adding a new item.

    Generally, an indexer does not modify the resource. The method is called "insert" but the indexer is only generating a key.

    The user might choose to add the item with a NAME derived from the KEY.
    """
    def __init__(self,
                 accessor,                # provides index accessors for the resource
                 name_to_key = lambda x:x # maps resource item NAMEs to KEYs
                 ):
        self.items = accessor
        self.name_to_key = name_to_key

    def insert(self,
               after=None, # NAME to insert after
               before=None # NAME to insert before
               ):
        match (after, before):
            case (None, None):  after  = self.items.last()
            case (None, _):     after  = self.items.before(before)
            case (_, None):     before = self.items.after(after)
        return generate_key_between(self.name_to_key(after), self.name_to_key(before))
    
    def insert_at_start(self): return self.insert(before=self.items.first())
    def insert_at_end(self): return self.insert(after=self.items.last())
    def __iter__(self):
        current = self.items.first()
        while current is not None:
            yield current
            current = self.items.after(current)

## External resource: SQLITE

"""
The Accessor methods after(),before(),first(),last() provide readonly access to the NAMEs of items in a resource.
"""

class SqliteAccessor:
    def __init__(self,
                 conn, # sqlite3 connection 
                 table, # table name
                 col='id' # column name
                 ):
        store_attr()

    def fetchone(self, m, where='', params=()):
        q = f"SELECT {m}({self.col}) FROM {self.table}"
        if where: q += f" WHERE {where}"
        r = self.conn.execute(q, params).fetchone()
        return r[0] if r else None

    def first(self): return self.fetchone('min')
    def last(self): return self.fetchone('max')
    def before(self, item): return self.fetchone('max', f"{self.col}<?", (item,))
    def after(self, item): return self.fetchone('min', f"{self.col}>?", (item,))

#
# The following methods would be neded intead, to support
# users accessing before/after information restricted
# to a part of the table via additional conditions in the where clause

    # def after(self, name, extra_where_condition=None):
    #     cond,vars = f"{self.col}>?", (name,)
    #     if extra_where_condition is not None:
    #         (sqlcond,value) = extra_where_condition
    #         cond += f' AND {sqlcond}'
    #         vars = tuple(list(vars) + [value])
    #     return self.fetchone('min', cond, vars)

    # def before(self, name, extra_where_condition=None):
    #     cond,vars = f"{self.col}<?", (name,)
    #     if extra_where_condition is not None:
    #         (sqlcond,value) = extra_where_condition
    #         cond += f' AND {sqlcond}'
    #         vars = tuple(list(vars) + [value])
    #     return self.fetchone('max', cond, vars)

class SqliteIndexer(Indexer):
    def __init__(self, 
                 conn, 
                 table, 
                 col='id',
                 name_to_key=lambda x:x # mapping which preserves key ordering
                 ):
        super().__init__(accessor=SqliteAccessor(conn, table, col),
                         name_to_key=name_to_key)

## Managed resource: a Python list

class ManagedListIndexer(Indexer):
    "Indexer which unusually owns and manages its resource, a Python list. Mainly, an implementation helper"
    def __init__(self,keys=[]):
        self.lst = ManagedListAccessor(keys)
        super().__init__(self.lst)
    def insert(self,after=None,before=None):
        new_idx = super().insert(after=after,before=before)
        self.lst.add(new_idx)
        return new_idx
    def __getitem__(self,key): return self.lst[key]
    def __len__(self): return len(self.lst)

class ManagedListAccessor(SortedList):
    "An accessor which, unusually, owns and manages its resource, a sorted Python list."
    def after(self, item):
        "Returns the next item after the specified item, or None if there is none."
        i = self.bisect_right(item)
        return self[i] if i<len(self) else None

    def before(self, item): 
        "Returns the previous item before the specified item, or None if there is none."
        i = self.bisect_left(item)-1
        return self[i] if i>=0 else None

    def first(self):
        "Returns the first item in the list, or None if empty."
        return self[0] if self else None

    def last(self):
        "Returns the last item in the list, or None if empty."
        return self[-1] if self else None

## External resouce: a directory of files

class FileAccessor:
    def __init__(self,
                 dir=".",               # Directory to scan for files
                 name_to_key=lambda x:x # Returns key given a valid file name. Else, None
                 ):
        self.name_to_key=name_to_key
        store_attr()

    def _key_names(self):
        "maps keys to valid file names in dir"
        retval = dict()
        names = [f.name for f in Path(self.dir).iterdir()]
        for name in names:
            key = self.name_to_key(name)
            if key is not None:
                retval[key] = name
        return retval

    def _keys(self): return ManagedListAccessor(self._key_names().keys())
    def _k_to_n(self,k): return None if k is None else self._key_names()[k]
    def _n_to_f_to_n(self,f,n): return self._k_to_n( f(n) )
    
    def after(self, name):
        in_k = self.name_to_key(name)
        out_k = self._keys().after(in_k)
        return None if out_k is None else self._key_names()[out_k]
    def before(self, name):
        in_k = self.name_to_key(name)
        out_k = self._keys().before(in_k)
        return None if out_k is None else self._key_names()[out_k]    
    def first(self):
        in_k = self._keys().first()
        return None if in_k is None else self._key_names()[in_k]
    def last(self):
        in_k = self._keys().last()
        return None if in_k is None else self._key_names()[in_k]
    
class FileIndexer(Indexer):
    def __init__(self, dir=".", name_to_key=lambda x:x):
        accessor = FileAccessor(dir, name_to_key)
        super().__init__(accessor=accessor, name_to_key=name_to_key)

