CREATE TABLE player (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    familyName TEXT NOT NULL,
    elo REAL NOT NULL,
    joiningDate timestamp
);
CREATE TABLE matchResult (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    playerA INTEGER,
    playerB INTEGER,
    result STRING,
    date timestamp,
    FOREIGN KEY(playerA) REFERENCES player(id),
    FOREIGN KEY(playerB) REFERENCES player(id)
);
CREATE TABLE history (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    player INTEGER,
    match INTEGER,
    eloBefore REAL NOT NULL,
    eloAfter REAL NOT NULL,
    FOREIGN KEY(player) REFERENCES player(id),
    FOREIGN KEY(match) REFERENCES match(id)
);
CREATE TABLE draft (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    active INTEGER,
    round INTEGER,
    date timestamp
);
CREATE TABLE draftPlayer (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    player INTEGER,
    draft INTEGER,
    rank INTEGER,
    active INTEGER,
    FOREIGN KEY(player) REFERENCES player(id),
    FOREIGN KEY(draft) REFERENCES draft(id)
);
CREATE TABLE draftMatch (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    match INTEGER,
    draft INTEGER,
    round INTEGER,
    FOREIGN KEY(match) REFERENCES match(id),
    FOREIGN KEY(draft) REFERENCES draft(id)
);
