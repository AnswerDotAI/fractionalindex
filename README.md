# FractionalIndex

## Overview

A `FractionalIndex` takes a list of existing items and allows you to insert a new item between any two existing items, or at the start or end.

Internally, it uses the `fractional_indexing` pypi package, which works as follows:

```python
first = generate_key_between(None, None) # 'a0'
second = generate_key_between(first, None) # 'a1' (after 1st)
third = generate_key_between(second, None) # 'a2' (after 2nd)
zeroth = generate_key_between(None, first) # 'Zz' (before 1st)
```

`FractionalIndex` differs with `fractional_indexing` in how it handles skipping the `before` or `after` parameters. If you only pass `before`, it will insert before the specified item, but after the largest item before that (if there is none, then it will insert at the start). If you only pass `after`, it will insert after the specified item, but before the smallest item after that (if there is none, then it will insert at the end).

```python
idx = FractionalIndex()
i1 = idx.insert() # starts a new index
print(i1) # 'a0'
i2 = idx.insert(after=i1) # inserts after i1
i3 = idx.insert(before=i2) # inserts before i2
i4 = idx.insert(i3, i2) # inserts between i3 and i2
i5 = idx.insert() # adds to the end
```

To add to the start, you can either pass the first item to `insert(before=...)`, or use `begin()`:

```python
i6 = idx.begin()
```

You can create an index from a list of existing items, which will be sorted:

```python
idx = FractionalIndex([i1, i2, i3, i4, i5, i6])
```

## Implementation

Internally, `FractionalIndex` by default uses `IndexingList`, a subclass of `sortedcontainers.SortedList` to store the items. The sort is needed so that `insert` without one of both of `after` or `before` can quickly find the next, previous or start/end item. The subclass adds the following methods (which are the only methods required by `FractionalIndex`):

- `after(item)`: returns the next item after the specified item, or `None` if there is none.
- `before(item)`: returns the previous item before the specified item, or `None` if there is none.
- `begin()`: returns the first item.
- `end()`: returns the last item.

## Alternative Implementations

FractionalIndex comes with a few alternative implementations.

### FileIndex

`FileIndex` uses `FileIndexing` instead of `IndexingList` internally. `FileIndexing` is a simple implementation which uses a list of files in a directory, to identify the correct locations in the index. For instance, consider the following directory contents:

```
a0-create-table.sql
a1-add-column.sql
a2-add-index.sql
```

In this case, we can create a suitable `FileIndex` with `idx = FileIndex(directory='.', separator='-')`. Since these are the default values, we can simply call `FileIndex()` to create it. Note that the directory will be re-scanned for the latest files on every method call.

You can then use it just like a regular FractionalIndex:

```python
idx = FileIndex(directory='migrations', separator='-')
new_id = idx.begin()  # Creates ID before first file
new_id = idx.insert()  # Creates ID after last file
new_id = idx.insert(after='a0')  # Creates ID between a0 and next file
new_id = idx.insert(before='a1')  # Creates ID between previous file and a1
new_id = idx.insert('a0', 'a1')  # Creates ID between a0 and a1
```

When you get a new ID, you'll need to create the corresponding file (e.g., `{new_id}-something.sql`) for it to be included in future operations.

### SqliteIndex

`SqliteIndex` indexes a sqlite DB table by using the `SqliteIndexing` class. Generally, the fractional index will be the primary key of the table. To use it, you need to pass a `Connection`, `table` and `column` (defaults to 'id') to the constructor:

```python
import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("CREATE TABLE migrations (id TEXT PRIMARY KEY)")

# Create the index
idx = SqliteIndex(conn, 'migrations', 'id')

# Use it like any other FractionalIndex
new_id = idx.begin()  # Creates ID before first row
new_id = idx.insert()  # Creates ID after last row
new_id = idx.insert(after='a0')  # Creates ID between a0 and next row
new_id = idx.insert(before='a1')  # Creates ID between previous row and a1
new_id = idx.insert('a0', 'a1')  # Creates ID between a0 and a1

# Don't forget to insert the new ID into your table
conn.execute("INSERT INTO migrations (id) VALUES (?)", (new_id,))
conn.commit()
```

Note that SqliteIndex will query the database on every operation to ensure it's working with the latest data, but it won't automatically insert new IDs - you need to do that yourself after getting a new ID.