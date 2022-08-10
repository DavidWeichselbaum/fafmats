import sqlite3 as sl

from .utils.pairing import get_draft_autopairing as get_draft_autopairing_con


def get_draft_autopairing(draft_player_numbers, player_ids, db_path):
    con = sl.connect(db_path)
    return get_draft_autopairing_con(draft_player_numbers, player_ids, con)
