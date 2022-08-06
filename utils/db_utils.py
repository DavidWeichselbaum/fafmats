import logging
import sqlite3 as sl
from datetime import datetime

from tabulate import tabulate

from constants import STARGING_ELO, INVERSE_RESULT_DICT, SQLITE_SCRIPT_PATH, DATABASE_PATH
from utils.utils import get_ascii_bar


log = logging.getLogger('db_utils')


def init_db():
    with open(SQLITE_SCRIPT_PATH) as sql_file:
        sql_script = sql_file.read()
    con = sl.connect(DATABASE_PATH)
    cursor = con.cursor()
    cursor.executescript(sql_script)
    return con


def add_player(first_name, last_name, con):
    sql = 'INSERT INTO player (name, familyName, elo, joiningDate) values(?, ?, ?, ?)'
    data = (first_name, last_name, STARGING_ELO, datetime.now())
    try:
        con.execute(sql, data)
    except sl.IntegrityError:
        log.error('Name already exists!')


def add_match(playerA_id, playerB_id, result, con):
    sql = 'INSERT INTO matchResult (playerA, playerB, result, date) values(?, ?, ?, ?)'
    data = (playerA_id, playerB_id, result, datetime.now())

    cursor = con.cursor()
    cursor.execute(sql, data)
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
            SELECT p1.name, p2.name, m.result, m.date FROM matchResult m
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
            SELECT p1.name, p2.name, m.result, m.date FROM matchResult m
                LEFT JOIN player p1
                    ON m.playerA = p1.id
                LEFT JOIN player p2
                    ON m.playerB = p2.id
                ORDER BY m.date
            """)
    return tabulate(data, headers=('player', 'player', 'result', 'date'), floatfmt='.0f')


def get_history_table(con, player_id, graph_width=100):
    data = con.execute("""
        SELECT p1.name, p2.name, m.result, m.date, h.eloAfter FROM history h
            LEFT JOIN matchResult m
                ON m.id = h.match
            LEFT JOIN player p1
                ON m.playerA = p1.id
            LEFT JOIN player p2
                ON m.playerB = p2.id
            WHERE h.player = ?
            ORDER BY m.date
        """, [player_id])

    player_name = get_player_name_by_id(player_id, con)
    sorted_data = []
    for playerA_name, playerB_name, result, date, elo_after in data:
        if playerA_name == player_name:
            sorted_data.append((playerA_name, playerB_name, result, date, elo_after))
        else:
            result = INVERSE_RESULT_DICT[result]
            sorted_data.append((playerB_name, playerA_name, result, date, elo_after))
    data = sorted_data

    all_elos = [row[4] for row in data]
    max_elo = max(all_elos)
    graph_increment = max_elo / graph_width

    graphed_data = []
    for playerA_name, playerB_name, result, date, elo_after in data:
        bar_string = get_ascii_bar(elo_after, graph_increment)
        graphed_data.append((playerA_name, playerB_name, result, date, elo_after, bar_string))

    return tabulate(graphed_data, headers=('player', 'player', 'result', 'date', 'elo', ''), floatfmt='.0f')


def add_draft(name, con):
    sql = 'INSERT INTO draft (name, active, date) values(?, ?, ?)'
    data = (name, True, datetime.now())

    cursor = con.cursor()
    try:
        cursor.execute(sql, data)
        draft_id = cursor.lastrowid
        return draft_id
    except sl.IntegrityError:
        log.error('Name already exists!')


def get_draft_id_by_name(name, con):
    sql = 'SELECT id FROM draft WHERE name = ?'
    data = [name]
    result = con.execute(sql, data)
    drafts = result.fetchall()
    if len(drafts) != 1:
        return None
    return drafts[0][0]


def get_draft_name_by_id(id_, con):
    sql = 'SELECT name FROM draft WHERE id = ?'
    data = [id_]
    result = con.execute(sql, data)
    drafts = result.fetchall()
    if len(drafts) != 1:
        return None
    return drafts[0][0]


def add_player_to_draft(player_id, draft_id, con):
    sql = 'INSERT INTO draftPlayer (player, draft, rank) values(?, ?, ?)'
    data = (player_id, draft_id, 0)
    try:
        con.execute(sql, data)
    except sl.IntegrityError:
        log.error('Player allready part of that draft!')


def get_drafts_table(con, draft_id=None, player_id=None):
    sql = 'SELECT name, active, date FROM draft'
    data = con.execute(sql)

    formatted_data = []
    for name, active, date in data:
        formatted_data.append((name, bool(active), date))
    return tabulate(formatted_data, headers=('name', 'active', 'date'))
