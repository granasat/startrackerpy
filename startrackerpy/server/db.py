import sqlite3


class Db:
    """Class DB to manage bursts
    """
    def __init__(self, db: str):
        self._db = db
        self._create_tables()

    def _create_tables(self) -> None:
        """Create burst table if it does not exists
        """
        conn = sqlite3.connect(self._db)
        c = conn.cursor()

        # Create table if it does not exists
        c.execute('''CREATE TABLE IF NOT EXISTS burst
        (id integer primary key, duration integer, interval integer,
        brightness integer, gamma integer, gain integer, exposure integer,
        progress integer default 0, inserted timestamp default (datetime('now','localtime')),
        updated timestamp default null, finished timestamp default null)''')
        conn.commit()
        conn.close()

    def insert_burst(self, duration: int, interval: int, brightness: int,
                     gamma: int, gain: int, exposure: int) -> int:
        """Insert a burst in the DB

        :param duration: Duration of the burst in seconds
        :param interval: Interval between frames in seconds
        :param brightness: Brightness value to set to the camera
        :param gamma: Gamma value to set to the camera
        :param gain: Gain value to set to the camera
        :param exposure: Exposure value to set to the camera

        :return: ID of the row inserted
        """
        conn = sqlite3.connect(self._db)
        c = conn.cursor()
        c.execute(
            """INSERT INTO burst(duration, interval, brightness, gamma, gain, exposure)
            VALUES(?,?,?,?,?,?)
            """, (duration, interval, brightness, gamma, gain, exposure))
        conn.commit()
        conn.close()

        return c.lastrowid

    def get_burst(self, burst_id: int) -> []:
        """Retrieve a burst

        :param burst_id: Row's ID of the burst

        :return: Row of the burst
        """
        res = []
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * from burst WHERE id=?", str(burst_id))
        res = [r for r in c]
        conn.close()

        if len(res) == 0:
            return []
        return res[0]

    def get_bursts(self) -> []:
        """Retrieve all the bursts

        :return: Rows of the bursts
        """
        res = []
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * from burst")
        res = [r for r in c]
        conn.close()

        return res

    def delete_burst(self, burst_id: int) -> None:
        """Delete a burst from the DB

        :param burst_id: ID of the burst to be deleted
        """
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("DELETE from burst WHERE id=?", str(burst_id))
        conn.commit()
        conn.close()

    def update_burst_progress(self, burst_id: int, progress: int) -> None:
        """Update progress of a burst

        :param burst_id: ID of the burst to be updated
        :param progress: Progress value
        """
        conn = sqlite3.connect(self._db)
        c = conn.cursor()
        if progress == 100:
            query = "UPDATE burst SET progress={}, updated=datetime('now','localtime'), " + \
                "finished=datetime('now','localtime') WHERE id={}"
        else:
            query = "UPDATE burst SET progress={}, updated=datetime('now','localtime') " + \
                "WHERE id={}"
        query = query.format(progress, burst_id)
        c.execute(query)
        conn.commit()
        conn.close()
