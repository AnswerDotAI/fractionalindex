mkdir -p fractionalindex
cat > fractionalindex/__init__.py << EOF
__all__ = ["FractionalIndex","FileIndex","SqliteIndex"]
EOF

cat > fractionalindex/fractionalindex.py << EOF
from sortedcontainers import SortedList
from fractional_indexing import generate_key_between
import os, sqlite3

class IndexingList(SortedList):
    def after(self, item):
        i = self.bisect_right(item)
        return self[i] if i<len(self) else None
    def before(self, item):
        i = self.bisect_left(item)-1
        return self[i] if i>=0 else None
    def begin(self):
        return self[0] if self else None
    def end(self):
        return self[-1] if self else None

class FractionalIndex:
    def __init__(self, items=None):
        self.items = IndexingList()
        if items:
            for i in items: self.items.add(i)
    def insert(self, before=None, after=None):
        if before and after: new = generate_key_between(before, after)
        elif before:
            l = self.items.before(before)
            r = before
            new = generate_key_between(l, r)
        elif after:
            l = after
            r = self.items.after(after)
            new = generate_key_between(l, r)
        else:
            l = self.items.end()
            r = None
            new = generate_key_between(l, r)
        self.items.add(new)
        return new
    def begin(self):
        b = self.items.begin()
        if not b: new = generate_key_between(None, None)
        else:
            l = self.items.before(b)
            r = b
            new = generate_key_between(l, r)
        self.items.add(new)
        return new

class FileIndex:
    def __init__(self, directory=".", separator="-", scan=True):
        self.dir, self.sep, self.scan = directory, separator, scan
        self._cache = None if scan else self._list_files()
    def _list_files(self):
        fs = []
        for f in os.listdir(self.dir):
            if self.sep in f: fs.append(f.split(self.sep)[0])
            else: fs.append(f)
        return sorted(fs)
    def _refresh(self):
        if self.scan: return self._list_files()
        else: return self._cache
    def after(self, item):
        fs = self._refresh()
        if item not in fs: return None
        i = fs.index(item)+1
        return fs[i] if i<len(fs) else None
    def before(self, item):
        fs = self._refresh()
        if item not in fs: return None
        i = fs.index(item)-1
        return fs[i] if i>=0 else None
    def begin(self):
        fs = self._refresh()
        return fs[0] if fs else None
    def end(self):
        fs = self._refresh()
        return fs[-1] if fs else None

def fetchone(conn, q, *ps):
    r = conn.execute(q, ps).fetchone()
    return r[0] if r else None

class SqliteIndex:
    def __init__(self, conn, table, column='id'):
        self.conn, self.table, self.col = conn, table, column
    def after(self, item):
        return fetchone(self.conn, f"SELECT min({self.col}) FROM {self.table} WHERE {self.col}>?", item)
    def before(self, item):
        return fetchone(self.conn, f"SELECT max({self.col}) FROM {self.table} WHERE {self.col}<?", item)
    def begin(self):
        return fetchone(self.conn, f"SELECT min({self.col}) FROM {self.table}")
    def end(self):
        return fetchone(self.conn, f"SELECT max({self.col}) FROM {self.table}")
EOF

mkdir -p tests
cat > tests/test_fractionalindex.py << EOF
import pytest, os, sqlite3
from fractionalindex.fractionalindex import FractionalIndex, FileIndex, SqliteIndex

def test_fractional_index_basic():
    idx = FractionalIndex()
    i1 = idx.insert()
    assert i1.startswith('a')
    i2 = idx.insert(after=i1)
    i3 = idx.insert(before=i2)
    i4 = idx.insert(i3, i2)
    i5 = idx.insert()
    lst = list(idx.items)
    assert len(lst)==5
    assert lst[0]==i1
    assert i2 in lst
    assert i3 in lst
    assert i4 in lst
    assert i5 in lst
    i6 = idx.begin()
    assert i6 < idx.items.begin()

def test_fractional_index_init_list():
    idx = FractionalIndex(['a0','a1','Zz'])
    assert list(idx.items)==['Zz','a0','a1']
    new = idx.insert(before='a0')
    assert list(idx.items)[1]==new
    new2 = idx.insert(after='a1')
    assert list(idx.items)[-1]==new2

def test_file_index(tmp_path):
    d = tmp_path / "files"
    d.mkdir()
    for i, nm in enumerate(["a0-create.sql","a1-update.sql","a2-index.sql"]):
        (d / nm).touch()
    fi = FileIndex(directory=d, separator='-')
    assert fi.begin()=='a0'
    assert fi.end()=='a2'
    assert fi.after('a0')=='a1'
    assert fi.before('a1')=='a0'

def test_sqlite_index():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id TEXT PRIMARY KEY, content TEXT)")
    conn.executemany("INSERT INTO test (id,content) VALUES (?,?)", [('a0','x'),('a1','y'),('Zz','z')])
    s = SqliteIndex(conn, 'test', 'id')
    assert s.begin()=='Zz'
    assert s.end()=='a1'
    assert s.after('Zz')=='a0'
    assert s.before('a1')=='a0'
EOF

cat > pyproject.toml << EOF
[project]
name = "fractionalindex"
version = "0.0.1"
description = "Fractional index library with multiple backends"
authors = [{name="Some Body"}]
dependencies = [
  "sortedcontainers",
  "fractional_indexing"
]

[project.optional-dependencies]
test = [
  "pytest",
]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
EOF

cat > NOTES.txt << EOF
All done! Run 'pip install .' or 'pip install -e .' then 'pytest' to test.
Then use 'twine upload dist/*' to release.
EOF
