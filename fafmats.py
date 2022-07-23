import os
import logging
import logging.config
from datetime import datetime

import coloredlogs
import sqlite3 as sl
from tabulate import tabulate


LOG_PATH = 'log'
DATABASE_PATH = 'data/data.db'

STARGING_ELO = 1000


def add_player(name, con):
    sql = 'INSERT INTO PLAYER (name, elo, joiningDate) values(?, ?, ?)'
    data = [(name, STARGING_ELO, datetime.now())]
    try:
        con.executemany(sql, data)
    except sl.IntegrityError:
        log.error('Name already exists!')


def add_match(playerA_id, playerB_id, result, con):
    sql = 'INSERT INTO MATCH (playerA, playerB, result, date) values(?, ?, ?, ?)'
    data = [(playerA_id, playerB_id, result, datetime.now())]
    con.executemany(sql, data)


def get_player_id_by_name(name, con):
    sql = 'SELECT id FROM PLAYER WHERE name = ?'
    data = [name]
    result = con.execute(sql, data)
    players = result.fetchall()
    if len(players) != 1:
        return None
    return players[0][0]


coloredlogs.DEFAULT_FIELD_STYLES['filename'] = {'color': 'magenta'}
logging.config.fileConfig(
    'logging.conf',
    disable_existing_loggers=False,
    defaults={'logfilename': LOG_PATH})
log = logging.getLogger('fafmats')


if not os.path.isfile(DATABASE_PATH):
    log.info('Add new database at {}'.format(DATABASE_PATH))
    con = sl.connect(DATABASE_PATH)
    con.execute("PRAGMA foreign_keys = 1")
    con.execute("""
            CREATE TABLE PLAYER (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                elo INTEGER NOT NULL,
                joiningDate timestamp
            );
        """)
    con.execute("""
            CREATE TABLE MATCH (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                playerA INTEGER,
                playerB INTEGER,
                result STRING,
                date timestamp,
                FOREIGN KEY(playerA) REFERENCES player(id),
                FOREIGN KEY(playerB) REFERENCES player(id)
            );
        """)
    con.commit()
else:
    log.info('Using database at {}'.format(DATABASE_PATH))
    con = sl.connect(DATABASE_PATH)


help_message = """
 h                              get help
 q                              quit
 p <NAME>                       add player
 P                              list players
 m <NAME> , <NAME> = <RESULT>   add 1v1 match with result (2:0, 2:1, 1:2, 0:2, draw, forfeit)
 M [<NAME>, ...]                list matches, optionally filtered for players
"""

input_count = 0
while True:
    try:
        input_ = input('[{:03d}]> '.format(input_count))

        flag = input_[0]
        input_string = input_[1:]
        input_string = input_string.lstrip()

        if flag == 'q':
            log.info('Quitting')
            break

        elif flag == 'h':
            log.info(help_message)

        elif flag == 'p':
            name = input_string.strip()
            if not name:
                log.error('Name needed!')
                continue

            add_player(name, con)

        elif flag == 'P':
            data = con.execute("SELECT name, elo, id, joiningDate FROM PLAYER")
            log.info('\n' + tabulate(data, headers=('name', 'elo', 'id', 'joined')))

        elif flag == 'm':
            input_strings = input_string.split('=')
            if len(input_strings) != 2:
                log.error('Need result!')
                continue
            players_string = input_strings[0].strip()
            result_string = input_strings[1].strip()
            player_strings = players_string.split(',')
            if len(player_strings) != 2:
                log.error('Need 2 players!')
                continue

            playerA_name, playerB_name = player_strings[0].strip(), player_strings[1].strip()
            playerA_id = get_player_id_by_name(playerA_name, con)
            playerB_id = get_player_id_by_name(playerB_name, con)

            if playerA_id == playerB_id:
                log.error('This is not solitaire, buddy!\nMinus 10 Elo :-)')
                continue

            log.info('Starting match between "{}" [{}] and "{}" [{}]'.format(
                playerA_name, playerA_id, playerB_name, playerB_id))

            add_match(playerA_id, playerB_id, result_string, con)

        elif flag == 'M':
            data = con.execute("""
                SELECT p1.name, p2.name, m.result, m.date FROM match m
                    LEFT JOIN player p1
                        ON m.playerA = p1.id
                    LEFT JOIN player p2
                        ON m.playerB = p2.id
                    ORDER BY m.date
                """)
            log.info('\n' + tabulate(data, headers=('player', 'player', 'result', 'date')))

        else:
            log.error('Not a flag: "{}"'.format(flag))

    except BaseException as error:
        log.error(error)
    else:
        con.commit()  # only commit stuff that worked :-)
    finally:
        input_count += 1
