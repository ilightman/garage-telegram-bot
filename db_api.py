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
        try:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM boxes")
                boxes = cur.fetchall()
                cur.close()
                return boxes
        except sqlite3.Error as error:
            logging.error("Error while getting all boxes", error)

    def create_box(self, box_name):
        try:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO boxes (box_name) VALUES (?)", (box_name,))
                box_id = cur.lastrowid
                cur.close()
                return box_id
        except sqlite3.Error as error:
            logging.error("Error while creating a new box", error)

    def delete_box(self, box_id):
        try:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM contents WHERE id=?", (box_id,))
                cur.execute("DELETE FROM boxes WHERE id=?", (box_id,))
                cur.close()
        except sqlite3.Error as error:
            logging.error(f"Error while deleting {box_id=}", error)

    def select_box(self, box_id, name: bool = False, place: bool = False):
        try:
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
        except sqlite3.Error as error:
            logging.error(f"Error while selecting {box_id=}", error)

    def select_content(self, content_id):
        try:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM contents WHERE content_id=?", (content_id,))
                content = cur.fetchone()
                cur.close()
                return content
        except sqlite3.Error as error:
            logging.error(f"Error while selecting {content_id=}", error)

    def update_content_by_content_id(self, content_id, value) -> str:
        try:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute("UPDATE contents SET contents = ? WHERE content_id = ? ;", (value, content_id))
                cur.close()
            content = self.select_content(content_id)
            return content[0]
        except sqlite3.Error as error:
            logging.error(f"Error while updating content by id {content_id=}", error)

    def select_all_contents(self, box_id, list_view: bool = False):
        try:
            with sqlite3.connect(self.name) as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM contents WHERE id=?", (box_id,))
                contents = cur.fetchall()
                cur.close()
                if list_view:
                    return '\n'.join([content[1] for content in contents])
                else:
                    return contents
        except sqlite3.Error as error:
            logging.error(f"Error while selecting all contents {box_id=}", error)


def add_contents_by_box_id(self, box_id, values: list):
    try:
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            for value in values:
                if len(value) >= 2:
                    cur.execute("INSERT INTO contents (id, contents) VALUES (?, ?)",
                                (box_id, value))
                else:
                    continue
            cur.close()
    except sqlite3.Error as error:
        logging.error(f"Error while adding contents by {box_id=}", error)


def delete_contents(self, content_id):
    try:
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM contents WHERE content_id=?", (content_id,))
            cur.close()
    except sqlite3.Error as error:
        logging.error(f"Error while deleting contents by {content_id}", error)


def update_name_or_place(self, box_id, value, name: bool = False, place: bool = False):  # , contents:bool = False
    sql = "UPDATE boxes SET "
    try:
        with sqlite3.connect(self.name) as conn:
            cur = conn.cursor()
            if name:
                cur.execute(sql + "box_name = ? WHERE id = ? ;", (value, box_id))
            elif place:
                cur.execute(sql + "place = ? WHERE id = ? ;", (value, box_id))
            cur.close()
        box = self.select_box(box_id)
        return box
    except sqlite3.Error as error:
        logging.error(f"Error while updating {name if name else place if place else ''}contents by {box_id}", error)


def search_in_box(self, item):
    try:
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
    except sqlite3.Error as error:
        logging.error(f"Error while searching {item=}", error)
