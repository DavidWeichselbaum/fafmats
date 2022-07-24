import logging
import sqlite3 as sl
from datetime import datetime

from tabulate import tabulate

from constants import STARGING_ELO, INVERSE_RESULT_DICT


log = logging.getLogger('db_utils')


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
    return tabulate(data, headers=('player', 'player', 'result', 'date'), floatfmt='.0f')


def get_history_table(con, player_id, graph_width=100):
    data = con.execute("""
        SELECT p1.name, p2.name, m.result, m.date, h.eloAfter FROM history h
            LEFT JOIN match m
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


def get_ascii_bar(count, increment):
    # https://alexwlchan.net/2018/05/ascii-bar-charts/

    bar_chunks, remainder = divmod(int(count * 8 / increment), 8)

    bar = '█' * bar_chunks
    if remainder > 0:
        bar += chr(ord('█') + (8 - remainder))
    bar = bar or '▏'

    return bar
