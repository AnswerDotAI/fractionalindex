from fastcore.utils import *
import sqlite3, tempfile
from pathlib import Path
from fractionalindex.fractionalindex import FractionalIndex, FileIndex, SqliteIndex

def test_fractional_index_basic():
    idx = FractionalIndex()
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
    i6 = idx.begin()
    assert i6<i1
    assert idx.items == [i6, i1, i3, i4, i2, i5]

def _test_index(idx, nms, add_func=noop):
    i1 = idx.begin()
    assert i1<nms[0]
    add_func(i1)
    i2 = idx.insert()
    assert i2>nms[-1]
    add_func(i2)
    i3 = idx.insert(before=i2)
    assert i3<i2 and i3>nms[-1]
    add_func(i3)
    i4 = idx.insert(after=nms[0])
    assert i4>nms[0] and i4<nms[1] 
    add_func(i4)
    i5 = idx.insert(before=nms[1])
    assert i5>nms[0] and i5<nms[1]
    add_func(i5)
    i6 = idx.insert(i4, i5)
    assert i6>i4 and i6<i5
    add_func(i6)
    i7 = idx.insert(nms[1], nms[2])
    assert i7>nms[1] and i7<nms[2]
    add_func(i7)

def test_fractional_index():
    nms = ['a2', 'a0', 'a1']
    idx = FractionalIndex(nms)
    nms.sort()
    assert idx.items==nms
    _test_index(idx, nms)

def test_file_index():
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        def add_file(nm): (d/f'{nm}-a').touch()
        nms = ['a0-create.sql','a1-update.sql','a2-index.sql']
        for nm in nms: (d/nm).touch()
        idx = FileIndex(d, sep='-')
        _test_index(idx, [o.split('-')[0] for o in nms], add_file)

def test_sqlite_index():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id TEXT PRIMARY KEY)")
    rows = [('Zz',),('a0',),('a1',)]
    conn.executemany("INSERT INTO test (id) VALUES (?)", rows)
    idx = SqliteIndex(conn, 'test', 'id')
    def add_row(i): conn.execute(f"INSERT INTO test (id) VALUES (?)", (i,))
    _test_index(idx, [o[0] for o in rows], add_row)
