CREATE TABLE player (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    familyName TEXT NOT NULL,
    elo REAL NOT NULL,
    joiningDate timestamp,
    isSelected Integer NOT NULL
);
CREATE TABLE game (
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
    game INTEGER,
    eloBefore REAL NOT NULL,
    eloAfter REAL NOT NULL,
    FOREIGN KEY(player) REFERENCES player(id),
    FOREIGN KEY(game) REFERENCES game(id)
);
CREATE TABLE draft (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
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
CREATE TABLE draftPairing (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    draft INTEGER,
    round INTEGER,
    playerA INTEGER,
    playerB INTEGER,
    FOREIGN KEY(draft) REFERENCES draft(id),
    FOREIGN KEY(playerA) REFERENCES player(id),
    FOREIGN KEY(playerB) REFERENCES player(id)
);
CREATE TABLE draftSuspension (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    draft INTEGER,
    round INTEGER,
    player INTEGER,
    FOREIGN KEY(draft) REFERENCES draft(id),
    FOREIGN KEY(player) REFERENCES player(id)
);
CREATE TABLE draftGame (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    game INTEGER,
    draft INTEGER,
    round INTEGER,
    FOREIGN KEY(game) REFERENCES game(id),
    FOREIGN KEY(draft) REFERENCES draft(id)
);
