import os
import logging
import logging.config
from traceback import format_exc
from datetime import datetime

import coloredlogs
import sqlite3 as sl
from tabulate import tabulate


LOG_PATH = 'log'
DATABASE_PATH = 'data/data.db'

STARGING_ELO = 1000
EXPECTED_TENFOLD_ADVANTAGE = 400  # at 400 elo difference, the stronger opponent should score 10 times higher on average
K_FACTOR = 32

RESULT_SCORE_DICT = {
    '2:0': 1,
    '2:1': 1,
    '1:2': 0,
    '0:2': 0,
    'draw': 0.5,
    'forfeit': 0.5}
WRONG_ORDER_RESULTS = ('0:2', '1:2')
INVERSE_RESULT_DICT = {
    '2:0': '0:2',
    '2:1': '1:2',
    '1:2': '2:1',
    '0:2': '2:0',
    'draw': 'draw',
    'forfeit': 'forfeit'}

YES_STRINGS = ['y', 'Y', 'yes', 'Yes']
NO_STRINGS = ['n', 'N', 'no', 'No']
SORT_METHOD_STRINGS = ('a', 'A', 'e', 'E', 'd', 'D')

HELP_MESSAGE = """
 h                              get help
 q                              quit
 p <NAME>                       add player
 P [<METHOD>]                   list players by method. a='alphabetical', e='elo', d='date'. Uppercase inverts.
 m <NAME> , <NAME> = <RESULT>   add 1v1 match with result (2:0, 2:1, 1:2, 0:2, draw, forfeit)
 M [<NAME>]                     list matches, optionally filtered for player
"""


def add_player(name, con):
    sql = 'INSERT INTO player (name, elo, joiningDate) values(?, ?, ?)'
    data = (name, STARGING_ELO, datetime.now())
    try:
        con.execute(sql, data)
    except sl.IntegrityError:
        log.error('Name already exists!')


def add_match(playerA_id, playerB_id, result, con):
    sql = 'INSERT INTO match (playerA, playerB, result, date) values(?, ?, ?, ?)'
    data = (playerA_id, playerB_id, result, datetime.now())

    cursor = con.cursor()
    con.execute(sql, data)
    match_id = cursor.lastrowid
    return match_id


def update_elo(player_id, elo_difference, match_id, con):
    elo_before = get_player_elo(player_id, con)
    elo_after = elo_before + elo_difference

    sql = 'INSERT INTO history (player, match, eloBefore, eloAfter) values(?, ?, ?, ?)'
    data = (player_id, match_id, elo_before, elo_after)
    con.execute(sql, data)

    sql = 'UPDATE player SET elo = ? WHERE id = ?'
    data = (elo_after, player_id)
    con.execute(sql, data)


def get_player_id_by_name(name, con):
    sql = 'SELECT id FROM player WHERE name = ?'
    data = [name]
    result = con.execute(sql, data)
    players = result.fetchall()
    if len(players) != 1:
        return None
    return players[0][0]


def get_player_name_by_id(id_, con):
    sql = 'SELECT name FROM player WHERE id = ?'
    data = [id_]
    result = con.execute(sql, data)
    players = result.fetchall()
    if len(players) != 1:
        return None
    return players[0][0]


def get_player_elo(id_, con):
    sql = 'SELECT elo FROM player WHERE id = ?'
    data = [id_]
    result = con.execute(sql, data)
    elo = result.fetchall()
    return elo[0][0]


def get_expected_elo_score(playerA_elo, playerB_elo):
    elo_difference = playerB_elo - playerA_elo
    return 1 / (1 + 10 ** (elo_difference / EXPECTED_TENFOLD_ADVANTAGE))


def get_elo_difference(playerA_elo, playerB_elo, result):
    playerA_score = RESULT_SCORE_DICT[result]
    playerA_expected_score = get_expected_elo_score(playerA_elo, playerB_elo)
    playerA_score_offset = playerA_score - playerA_expected_score
    elo_difference = K_FACTOR * playerA_score_offset
    return elo_difference


def get_players_table(con, method):
    if method == 'd':
        sort_string = 'ORDER BY joiningDate ASC'
    elif method == 'D':
        sort_string = 'ORDER BY joiningDate DESC'
    elif method == 'a':
        sort_string = 'ORDER BY name ASC'
    elif method == 'A':
        sort_string = 'ORDER BY name DESC'
    elif method == 'e':
        sort_string = 'ORDER BY elo ASC'
    elif method == 'E':
        sort_string = 'ORDER BY elo DESC'

    data = con.execute("SELECT name, elo, id, joiningDate FROM player {}".format(sort_string))
    return tabulate(data, headers=('name', 'elo', 'id', 'joined'), floatfmt=".0f")


def get_matches_table(con, player_id=None):
    if player_id is not None:
        data = con.execute("""
            SELECT p1.name, p2.name, m.result, m.date FROM match m
                LEFT JOIN player p1
                    ON m.playerA = p1.id
                LEFT JOIN player p2
                    ON m.playerB = p2.id
                WHERE m.playerA = ? OR m.playerB = ?
                ORDER BY m.date
            """, [player_id, player_id])

        player_name = get_player_name_by_id(player_id, con)
        sorted_data = []
        for playerA_name, playerB_name, result, date in data:
            if playerA_name == player_name:
                sorted_data.append((playerA_name, playerB_name, result, date))
            else:
                result = INVERSE_RESULT_DICT[result]
                sorted_data.append((playerB_name, playerA_name, result, date))
        data = sorted_data
    else:
        data = con.execute("""
            SELECT p1.name, p2.name, m.result, m.date FROM match m
                LEFT JOIN player p1
                    ON m.playerA = p1.id
                LEFT JOIN player p2
                    ON m.playerB = p2.id
                ORDER BY m.date
            """)
    return tabulate(data, headers=('player', 'player', 'result', 'date'))


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
else:
    log.info('Using database at {}'.format(DATABASE_PATH))
    con = sl.connect(DATABASE_PATH)


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
            log.info(HELP_MESSAGE)

        elif flag == 'p':
            name = input_string.strip()
            if not name:
                log.error('Name needed!')
                continue

            while True:
                confirmation_string = input('[{:03d}] Add player "{}"? [y/n] > '.format(input_count, input_string))
                if confirmation_string in YES_STRINGS:
                    add_player(name, con)
                    break
                elif confirmation_string in NO_STRINGS:
                    break

        elif flag == 'P':
            if not input_string:
                input_string = 'a'
            elif input_string not in SORT_METHOD_STRINGS:
                log.error('Incorrect sort method')
                continue

            player_table = get_players_table(con, input_string)
            log.info('\n' + player_table)

        elif flag == 'm':
            input_strings = input_string.split('=')
            if len(input_strings) != 2:
                log.error('Need result!')
                continue
            players_string = input_strings[0].strip()
            result_string = input_strings[1].strip()
            if result_string not in RESULT_SCORE_DICT:
                log.error('Result must be one of {}'.format(RESULT_SCORE_DICT.keys()))
                continue

            player_strings = players_string.split(',')
            if len(player_strings) != 2:
                log.error('Need 2 players!')
                continue

            playerA_name, playerB_name = player_strings[0].strip(), player_strings[1].strip()

            if result_string in WRONG_ORDER_RESULTS:
                result_string = INVERSE_RESULT_DICT[result_string]
                playerA_name, playerB_name, = playerB_name, playerA_name

            playerA_id = get_player_id_by_name(playerA_name, con)
            playerB_id = get_player_id_by_name(playerB_name, con)

            if playerA_id is None:
                log.error('Player "{}" does not exist. Too bad.'.format(playerA_name))
                continue
            if playerB_id is None:
                log.error('Player "{}" does not exist. Lolnope.'.format(playerB_name))
                continue
            if playerA_id == playerB_id:
                log.error('This is not solitaire, buddy!\nMinus 10 Elo :-)')
                continue

            playerA_elo = get_player_elo(playerA_id, con)
            playerB_elo = get_player_elo(playerB_id, con)
            elo_difference = get_elo_difference(playerA_elo, playerB_elo, result_string)
            playerA_elo_new = playerA_elo + elo_difference
            playerB_elo_new = playerB_elo - elo_difference

            playerA_elo_sign = '+' if elo_difference >= 0 else '-'
            playerB_elo_sign = '+' if elo_difference <= 0 else '-'
            log.info('Adding match:\n{}: {} {} {} = {} elo\n{}: {} {} {} = {} elo".'.format(
                playerA_name, playerA_elo, playerA_elo_sign, abs(elo_difference), playerA_elo_new,
                playerB_name, playerB_elo, playerB_elo_sign, abs(elo_difference), playerB_elo_new))

            while True:
                confirmation_string = input('[{:03d}] Add Result? [Y/n] > '.format(input_count))
                if confirmation_string in YES_STRINGS + ['']:
                    log.info('Accepted Result')
                    match_id = add_match(playerA_id, playerB_id, result_string, con)
                    update_elo(playerA_id, elo_difference, match_id, con)
                    update_elo(playerB_id, - elo_difference, match_id, con)
                    break
                elif confirmation_string in NO_STRINGS:
                    log.info('Rejected Result')
                    break
                else:
                    log.info('ENGLISH! DO. YOU. SPEAK. IT???')
                    continue

        elif flag == 'M':
            player_id = None
            if input_string:
                player_id = get_player_id_by_name(input_string, con)
                if player_id is None:
                    log.error('Did not find that person!')
                    continue
            matches_table = get_matches_table(con, player_id)
            log.info('\n' + matches_table)

        else:
            log.error('Not a flag: "{}"'.format(flag))

    except KeyboardInterrupt:
        log.warning('User "q" to quit.')
    except BaseException:
        log.error(format_exc())
    else:
        con.commit()  # only commit stuff that worked :-)
    finally:
        input_count += 1
