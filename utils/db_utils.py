import logging
import sqlite3 as sl
from datetime import datetime

from tabulate import tabulate

from constants import STARGING_ELO, INVERSE_RESULT_DICT, SQLITE_SCRIPT_PATH, DATABASE_PATH
from utils.utils import get_ascii_bar
from utils.elo import calculate_fafmats_scores
# from utils.pairing import get_player_pairings


log = logging.getLogger('db_utils')


def init_db():
    with open(SQLITE_SCRIPT_PATH) as sql_file:
        sql_script = sql_file.read()
    con = sl.connect(DATABASE_PATH)
    cursor = con.cursor()
    cursor.executescript(sql_script)
    return con


def add_player(first_name, last_name, con):
    sql = 'INSERT INTO player (name, familyName, elo, joiningDate, isSelected) values(?, ?, ?, ?, ?)'
    data = (first_name, last_name, STARGING_ELO, datetime.now(), True)
    try:
        con.execute(sql, data)
    except sl.IntegrityError:
        log.error('Name already exists!')


def add_game(playerA_id, playerB_id, result, con):
    sql = 'INSERT INTO game (playerA, playerB, result, date) values(?, ?, ?, ?)'
    data = (playerA_id, playerB_id, result, datetime.now())

    cursor = con.cursor()
    cursor.execute(sql, data)
    game_id = cursor.lastrowid
    return game_id


def get_player_ids_by_game(game_id, con):
    sql = 'SELECT id FROM game WHERE id = ?'
    data = [game_id]
    result = con.execute(sql, data)
    players = result.fetchall()
    print(players)
    if len(players) != 1:
        return None
    return players[0][0]


def update_elo(player_id, elo_difference, game_id, con):
    elo_before = get_player_elo(player_id, con)
    elo_after = elo_before + elo_difference

    sql = 'INSERT INTO history (player, game, eloBefore, eloAfter) values(?, ?, ?, ?)'
    data = (player_id, game_id, elo_before, elo_after)
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


def get_all_player_ids(con):
    sql = 'SELECT id FROM player'
    result = con.execute(sql)
    player_id_tupels = result.fetchall()
    player_ids = [player_id_tuple[0] for player_id_tuple in player_id_tupels]
    return player_ids


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


def get_games_table(con, player_id=None):
    if player_id is not None:
        data = con.execute("""
            SELECT p1.name, p2.name, m.result, m.date FROM game m
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
            SELECT p1.name, p2.name, m.result, m.date FROM game m
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
            LEFT JOIN game m
                ON m.id = h.game
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
    sql = 'INSERT INTO draft (name, active, round, date) values(?, ?, ?, ?)'
    data = (name, True, 1, datetime.now())

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
    sql = 'INSERT INTO draftPlayer (player, draft, rank, active) values(?, ?, ?, ?)'
    data = (player_id, draft_id, 0, 1)
    try:
        con.execute(sql, data)
    except sl.IntegrityError:
        log.error('Player allready part of that draft!')


def get_drafts_table(con, player_id=None, draft_id=None):
    if player_id is None and draft_id is None:
        sql = 'SELECT d.id, d.name, d.active, d.round, d.date FROM draft d'
        data = con.execute(sql)
    elif player_id is not None:
        sql = """
            SELECT d.id, d.name, d.active, d.round, d.date FROM draft d
                LEFT JOIN draftPlayer p
                    ON d.id = p.draft
                WHERE p.player = ?
                ORDER BY d.date
            """
        result = con.execute(sql, [player_id])
        data = result.fetchall()
    elif draft_id is not None:
        sql = """
            SELECT d.id, d.name, d.active, d.round, d.date FROM draft d
                WHERE d.id = ?
            """
        result = con.execute(sql, [draft_id])
        data = result.fetchall()

    formatted_data = []
    for id_, name, active, round_, date in data:
        formatted_data.append((id_, name, bool(active), round_, date))
    return tabulate(formatted_data, headers=('id', 'name', 'active', 'round', 'date'))


def get_draft_table(draft_id, con):
    draft_table = get_drafts_table(con, draft_id=draft_id)
    player_table = get_draft_player_table(draft_id, con)

    return_string = '#### Draft:\n{}\n\n#### Players:\n{}'.format(draft_table, player_table)
    return return_string


def get_elo_difference(playerA_id, playerB_id, con):
    playerA_elo = get_player_elo(playerA_id, con)
    playerB_elo = get_player_elo(playerB_id, con)
    return playerB_elo - playerA_elo


def get_fafmats_scores(player_id, opponent_ids, con):
    elo_differences, n_encounters_list = [], []
    for opponent_id in opponent_ids:
        elo_difference = abs(get_elo_difference(player_id, opponent_id, con))
        n_encounters = get_n_encounters(player_id, opponent_id, con)
        elo_differences.append(elo_difference)
        n_encounters_list.append(n_encounters)

    return calculate_fafmats_scores(elo_differences, n_encounters_list)


def get_n_encounters(playerA_id, playerB_id, con):
    data = (playerA_id, playerB_id, playerB_id, playerA_id)
    result = con.execute("""
        SELECT m.date FROM game m
            WHERE m.playerA = ? AND m.playerB = ? OR m.playerA = ? AND m.playerB = ?
            ORDER BY m.date
        """, data)
    player_results = result.fetchall()
    return len(player_results)


def get_draft_players(draft_id, con):
    sql = """
        SELECT dp.player FROM draftPlayer dp
            WHERE dp.draft = ?
            ORDER BY dp.rank
        """
    result = con.execute(sql, [draft_id])
    data = result.fetchall()
    player_ids = [player_tuple[0] for player_tuple in data]
    return player_ids


def get_draft_player_table(draft_id, con):
    sql = """
        SELECT p.name, dp.rank, dp.active FROM draftPlayer dp
            LEFT JOIN draft d
                ON dp.draft = d.id
            LEFT JOIN player p
                ON dp.player = p.id
            WHERE d.id = ?
            ORDER BY dp.rank
        """
    result = con.execute(sql, [draft_id])
    data = result.fetchall()

    formatted_data = []
    for name, rank, active in data:
        formatted_data.append((name, rank, bool(active)))
    return tabulate(formatted_data, headers=('name', 'rank', 'active'))


def get_round_by_draft_id(draft_id, con):
    sql = 'SELECT d.round FROM draft d WHERE d.id = ?'
    result = con.execute(sql, [draft_id])
    round_ = result.fetchall()
    return round_[0][0]


def get_active_draft_players(draft_id, con):
    sql = """
        SELECT p.id FROM draftPlayer dp
            LEFT JOIN draft d
                ON dp.draft = d.id
            LEFT JOIN player p
                ON dp.player = p.id
            WHERE d.id = ? AND dp.active > 0
            ORDER BY dp.rank
        """
    result = con.execute(sql, [draft_id])
    data = result.fetchall()
    player_ids = [item[0] for item in data]
    return player_ids


def get_n_wins(player_id, draft_id, con):
    pass


def add_suspended_draft_player(player_id, draft_id, round_, con):
    sql = 'INSERT INTO draftSuspension (draft, round, player) values(?, ?, ?)'
    data = (draft_id, round_, player_id)
    con.execute(sql, data)


def add_pairing_draft_players(playerA_id, playerB_id, draft_id, round_, con):
    sql = 'INSERT INTO draftPairing (draft, round, playerA, playerB) values(?, ?, ?, ?)'
    data = (draft_id, round_, playerA_id, playerB_id)
    con.execute(sql, data)


def add_player_draft_pairing(player_pairings, draft_id, round_, con):
    paired_player_pairs = [pairing for pairing in player_pairings if len(pairing) == 2]
    suspended_player_ids = [pairing for pairing in player_pairings if len(pairing) == 1]

    for paired_player_ids in paired_player_pairs:
        playerA_id = paired_player_ids[0]
        playerB_id = paired_player_ids[1]
        add_pairing_draft_players(playerA_id, playerB_id, draft_id, round_, con)

    for suspended_player_id_tuple in suspended_player_ids:
        suspended_player_id = suspended_player_id_tuple[0]
        add_suspended_draft_player(suspended_player_id, draft_id, round_, con)


def get_draft_pairings_by_draft_id(draft_id, round_, con):
    sql = """
        SELECT dp.playerA, dp.playerB FROM draftPairing dp
            WHERE dp.draft = ? AND dp.round = ?
        """
    result = con.execute(sql, [draft_id, round_])
    pairings = result.fetchall()
    return pairings


def get_draft_suspensions_by_draft_id(draft_id, round_, con):
    sql = """
        SELECT dp.player FROM draftSuspension dp
            WHERE dp.draft = ? AND dp.round = ?
        """
    result = con.execute(sql, [draft_id, round_])
    data = result.fetchall()
    player_ids = [player_id_tuple[0] for player_id_tuple in data]
    return player_ids


def delete_pairings_by_draft_id(draft_id, round_, con):
    sql = """
        DELETE FROM draftPairing
            WHERE draft = ? AND round = ?
        """
    con.execute(sql, [draft_id, round_])


def delete_suspensions_by_draft_id(draft_id, round_, con):
    sql = """
        DELETE FROM draftSuspension
            WHERE draft = ? AND round = ?
        """
    con.execute(sql, [draft_id, round_])


def add_game_id_to_draft(game_id, draft_id, draft_round, con):
    sql = 'INSERT INTO draftGame (game, draft, round) values(?, ?, ?)'
    data = (game_id, draft_id, draft_round)
    con.execute(sql, data)
