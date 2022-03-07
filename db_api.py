import sqlite3
import logging


class DB:

    def __init__(self, name):
        self.name = name

    def create_db(self):
        try:
            sql = """CREATE TABLE IF NOT EXISTS boxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_name TEXT UNIQUE,
            place TEXT
            );"""
            sql2 = """CREATE TABLE IF NOT EXISTS contents (
                        id INTEGER,
                        contents TEXT,
                        content_id INTEGER PRIMARY KEY AUTOINCREMENT
                        );"""
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                logging.info("Successfully Connected to SQLite")
                cur.execute(sql)
                logging.info("SQLite boxes table created")
                cur.execute(sql2)
                logging.info("SQLite contents table created")
                cur.close()
        except sqlite3.Error as error:
            logging.error("Error while creating a sqlite table", error)

    def get_all_box(self):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM boxes")
            boxes = cur.fetchall()
            cur.close()
            return boxes

    def create_box(self, box_name):

        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO boxes (box_name) VALUES (?)", (box_name,))
            box_id = cur.lastrowid
            cur.close()
            return box_id

    def delete_box(self, box_id):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM contents WHERE id=?", (box_id,))
            cur.execute("DELETE FROM boxes WHERE id=?", (box_id,))
            cur.close()

    def select_box(self, box_id, name: bool = False, place: bool = False):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM boxes WHERE id=?", (box_id,))
            box = cur.fetchone()
            cur.close()
            if name:
                return box[1]
            elif place:
                return box[2]
            else:
                return box

    def select_content(self, content_id):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM contents WHERE content_id=?", (content_id,))
            content = cur.fetchone()
            cur.close()
            return content

    def update_content_by_content_id(self, content_id, value) -> str:
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE contents SET contents = ? WHERE content_id = ? ;", (value, content_id))
            cur.close()
        content = self.select_content(content_id)
        return content[0]

    def select_all_contents(self, box_id, list_view: bool = False):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM contents WHERE id=?", (box_id,))
            contents = cur.fetchall()
            cur.close()
            if list_view:
                return '\n'.join([content[1] for content in contents])
            else:
                return contents

    def add_contents_by_box_id(self, box_id, values: list):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            for value in values:
                if len(value) >= 2:
                    cur.execute("INSERT INTO contents (id, contents) VALUES (?, ?)",
                                (box_id, value))
                else:
                    continue
            cur.close()

    def delete_contents(self, content_id):
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM contents WHERE content_id=?", (content_id,))
            cur.close()

    def update_name_or_place(self, box_id, value, name: bool = False, place: bool = False):  # , contents:bool = False
        sql = "UPDATE boxes SET "
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            if name:
                cur.execute(sql + "box_name = ? WHERE id = ? ;", (value, box_id))
            elif place:
                cur.execute(sql + "place = ? WHERE id = ? ;", (value, box_id))
            cur.close()
        box = self.select_box(box_id)
        return box

    def search_in_box(self, item):
        sql = 'SELECT * FROM contents WHERE contents LIKE ? '
        if len(item) < 3:
            return []
        else:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute(sql, ('%' + item.lower() + '%',))
                contents = cur.fetchall()
                if contents:
                    boxes_id = set(item[0] for item in contents)
                    sql2 = '(' + ','.join('?' * len(boxes_id)) + ')'
                    sql = f"SELECT * FROM boxes WHERE id IN "  # {tuple(boxes_id)}
                    cur.execute(sql + sql2, tuple(boxes_id))
                    boxes = cur.fetchall()
                    cur.close()
                    return boxes
