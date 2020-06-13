import sqlite3


class Db():
    def __init__(self, db):
        self._db = db
        self._create_tables()

    def _create_tables(self):
        conn = sqlite3.connect(self._db)
        c = conn.cursor()

        # Create table if it does not exists
        c.execute('''CREATE TABLE IF NOT EXISTS burst
        (id integer primary key, duration integer, interval integer,
        brightness integer, gamma integer, gain, exposure,
        progress integer default 0, inserted timestamp default (datetime('now','localtime')),
        updated timestamp default null, finished timestamp default null)''')
        conn.commit()
        conn.close()

    def insert_burst(self, duration, interval, gamma, gain, exposure):
        conn = sqlite3.connect(self._db)
        c = conn.cursor()
        c.execute(
            """INSERT INTO burst(duration, interval, brightness, gamma, gain, exposure)
            VALUES(?,?,?,?,?,?)
            """, (duration, interval, gamma, gain, exposure))
        conn.commit()
        conn.close()

        return c.lastrowid

    def get_bursts(self):
        res = []
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * from burst")
        res = [r for r in c]
        conn.close()

        return res

    def delete_burst(self, id):
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("DELETE from burst WHERE id=?", id)
        conn.commit()
        conn.close()

    def update_burst_progress(self, id, progress):
        conn = sqlite3.connect(self._db)
        c = conn.cursor()
        if progress == 100:
            query = "UPDATE burst SET progress={}, updated=datetime('now','localtime'), " + \
                "finished=datetime('now','localtime') WHERE id={}"
        else:
            query = "UPDATE burst SET progress={}, updated=datetime('now','localtime') " + \
                "WHERE id={}"
        query = query.format(id, progress)
        c.execute(query)
        conn.commit()
        conn.close()
