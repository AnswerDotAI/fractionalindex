from fastcore.utils import *
import sqlite3, tempfile
from pathlib import Path
from fractionalindex.fractionalindex import *


def test_managed_list_indexer():
    idx = ManagedListIndexer()
    i1 = idx.insert()
    assert i1.startswith('a')
    i2 = idx.insert(after=i1)
    assert i2>i1
    i3 = idx.insert(before=i2)
    assert i3<i2 and i3>i1
    i4 = idx.insert(i3, i2)
    assert i4>i3 and i4<i2
    i5 = idx.insert()
    lst = list(idx.items)
    assert i5 in lst and i5>i2
    assert len(lst)==5
    i6 = idx.insert_at_start()
    assert i6<i1
    assert idx.items == [i6, i1, i3, i4, i2, i5]

def _test_indexer(idx,
                  add_func=noop # takes a key, creates the item, returns its name 
                  ):
    i1 = idx.insert()
    i1name = add_func(i1)
    assert i1.startswith('a')

    i2 = idx.insert(after=i1name)
    i2name = add_func(i2)
    assert i2>i1

    i3 = idx.insert(before=i2name)
    i3name = add_func(i3)
    assert i1<i3 
    assert i3<i2

    i4 = idx.insert(i3name, i2name)
    i4name = add_func(i4)
    assert i4>i3 and i4<i2

    i5 = idx.insert()
    i5name = add_func(i5)
    assert i5>i2
    lst = list(idx) #
    assert len(lst)==5

    i6 = idx.insert_at_start()
    i6name = add_func(i6)
    assert i6<i1
    assert list(idx) == [i6name, i1name, i3name, i4name, i2name, i5name]

def test_named_file_indexer():
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        def add_file(key): 
            name = f'{key}--a' 
            (d/name).touch()
            return name
        def get_key_from_name(name):
            if name is not None and '--' in name: return name.split('--')[0]
            else: return None
        idx = FileIndexer(d,get_key_from_name)
        _test_indexer(idx, add_file)

def test_sqlite_indexer():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id TEXT PRIMARY KEY)")
    idx = SqliteIndexer(conn, table='test', col='id')
    def name_to_key(name): return name
    def add_record(key):
        conn.execute("INSERT INTO test (id) VALUES (?)", (key,))
        return key
    _test_indexer(idx, add_record)

def test_sqlite_indexer_with_names():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id TEXT PRIMARY KEY)")
    def name_to_key(name): 
        return name.split('-')[1] if (name is not None and '-' in name) else None
    idx = SqliteIndexer(conn, table='test', col='id',name_to_key=name_to_key)
    def add_record(key):
        name = f"msg-{key}"
        conn.execute("INSERT INTO test (id) VALUES (?)", (name,))
        return name
    _test_indexer(idx, add_record)

def test_managed_list():
    "Initializing a managed list indexer with a list"
    nms = ['a2', 'a0', 'a1'] # out of order
    idx = ManagedListIndexer(nms)
    nms.sort()
    assert list(idx)==nms
    _test_indexer_with_initial_names(idx, nms)


def _test_indexer_with_initial_names(idx, initial_names, add_func=noop):
    "Tests any Indexer, assuming the resource starts with initial_names"
    i1 = idx.insert_at_start()
    assert i1<initial_names[0]
    add_func(i1)
    i2 = idx.insert_at_end()
    assert i2>initial_names[-1]
    add_func(i2)
    i3 = idx.insert(before=i2)
    assert i3<i2 and i3>initial_names[-1]
    add_func(i3)
    i4 = idx.insert(after=initial_names[0])
    assert i4>initial_names[0] and i4<initial_names[1] 
    add_func(i4)
    i5 = idx.insert(before=initial_names[1])
    assert i5>initial_names[0] and i5<initial_names[1]
    add_func(i5)
    i6 = idx.insert(i4, i5)
    assert i6>i4 and i6<i5
    add_func(i6)
    i7 = idx.insert(initial_names[1], initial_names[2])
    assert i7>initial_names[1] and i7<initial_names[2]
    add_func(i7)

def test_managed_list_with_initial_names():
    "Initializing a managed list indexer with a list"
    nms = ['a2', 'a0', 'a1'] # out of order
    idx = ManagedListIndexer(nms)
    _test_indexer_with_initial_names(idx, sorted(nms))

