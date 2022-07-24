import sqlite3 as sl

from constants import DATABASE_PATH


def init_db():
    con = sl.connect(DATABASE_PATH)
    con.execute("PRAGMA foreign_keys = 1")

    con.execute("""
            CREATE TABLE player (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                elo REAL NOT NULL,
                joiningDate timestamp
            );
        """)

    con.execute("""
            CREATE TABLE match (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                playerA INTEGER,
                playerB INTEGER,
                result STRING,
                date timestamp,
                FOREIGN KEY(playerA) REFERENCES player(id),
                FOREIGN KEY(playerB) REFERENCES player(id)
            );
        """)

    con.execute("""
            CREATE TABLE history (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                player INTEGER,
                match INTEGER,
                eloBefore REAL NOT NULL,
                eloAfter REAL NOT NULL,
                FOREIGN KEY(player) REFERENCES player(id),
                FOREIGN KEY(match) REFERENCES match(id)
            );
        """)

    con.commit()
    return con
