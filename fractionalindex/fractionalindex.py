from sortedcontainers import SortedList
from fractional_indexing import generate_key_between
from fastcore.utils import *

class IndexingList(SortedList):
    "A subclass of SortedList that adds methods for finding the next/previous items and the first/last items in the list."
    def after(self, item):
        "Returns the next item after the specified item, or None if there is none."
        i = self.bisect_right(item)
        return self[i] if i<len(self) else None

    def before(self, item): 
        "Returns the previous item before the specified item, or None if there is none."
        i = self.bisect_left(item)-1
        return self[i] if i>=0 else None

    def begin(self):
        "Returns the first item in the list, or None if empty."
        return self[0] if self else None

    def end(self):
        "Returns the last item in the list, or None if empty."
        return self[-1] if self else None

class FractionalIndexBase:
    "Manages a sorted list of version strings and allows inserting new versions between existing ones."
    def __init__(self,
                 items=None, # Optional list of version strings to initialize with
                 idxlist=None # Optional IndexingList to initialize with
                 ):
        self.items = idxlist or IndexingList(items or [])

    def insert(self,
               after=None, # Item to insert after
               before=None # Item to insert before
               ):
        """Insert a new item between the specified items.
        
        If only after is specified, inserts after that item but before the next item.
        If only before is specified, inserts before that item but after the previous item.
        If neither is specified, adds to the end."""
        if after and not before: before = self.items.after(after)
        elif before and not after: after = self.items.before(before)
        elif not after and not before: after = self.items.end()
        return self.add(generate_key_between(after, before))

    def begin(self):
        "Insert a new item at the start of the list."
        b = self.items.begin()
        return self.add(generate_key_between(None, b))

    def add(self, item):
        "Add a new item to the list."
        return item


class FractionalIndex(FractionalIndexBase):
    def add(self, item):
        self.items.add(item)
        return item

    def __getitem__(self, i): return self.items[i]
    def __len__(self): return len(self.items)


class FileIndexing:
    def __init__(self,
                 dir=".", # Directory to scan for files
                 sep="-" # Separator between version and rest of filename 
                 ):
        store_attr()

    def _list(self): return IndexingList([f.name.split(self.sep)[0] for f in Path(self.dir).iterdir()])
    def after(self, item): return self._list().after(item)
    def before(self, item): return self._list().before(item)
    def begin(self): return self._list().begin()
    def end(self): return self._list().end()


class FileIndex(FractionalIndexBase):
    def __init__(self, dir=".", sep="-"):
        idxlist = FileIndexing(dir, sep)
        super().__init__(idxlist=idxlist)

class SqliteIndexing:
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

    def after(self, item): return self.fetchone('min', f"{self.col}>?", (item,))
    def before(self, item): return self.fetchone('max', f"{self.col}<?", (item,))
    def begin(self): return self.fetchone('min')
    def end(self): return self.fetchone('max')


class SqliteIndex(FractionalIndexBase):
    def __init__(self, conn, table, col='id'): super().__init__(idxlist=SqliteIndexing(conn, table, col))
