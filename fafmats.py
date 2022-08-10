import os
import logging
import logging.config
from traceback import format_exc

import coloredlogs
import sqlite3 as sl

from constants import LOG_PATH, DATABASE_PATH
from utils.db_utils import init_db
from utils.cli_utils import handle_add_player, handle_add_game, \
    handle_show_players, handle_show_games, handle_show_history, handle_show_drafts, \
    handle_draft, handle_show_score


coloredlogs.DEFAULT_FIELD_STYLES['filename'] = {'color': 'magenta'}
logging.config.fileConfig(
    'logging.conf',
    disable_existing_loggers=False,
    defaults={'logfilename': LOG_PATH})
log = logging.getLogger('fafmats')


if not os.path.isfile(DATABASE_PATH):
    log.info('Add new database at {}'.format(DATABASE_PATH))
    con = init_db()
else:
    log.info('Using database at {}'.format(DATABASE_PATH))
    con = sl.connect(DATABASE_PATH)


HELP_MESSAGE = """
 h                              get help
 q                              quit
 p <FIRST_NAME> <LAST_NAME>     add player
 P [<METHOD>]                   list players by method.
                                methods:
                                  'a/A': alphabetical
                                  'e/E': elo
                                  'd/D': date
 g <NAME> <NAME> <RESULT>       add 1v1 game between named players.
                                possible results: '2:0', '2:1', '1:2', '0:2', 'draw', 'forfeit'
 G [<NAME>]                     list games, optionally filtered for player
 G <NAME>                       show elo history of player
 d [<NAME/ID>] [<ACTION>]       start (named) draft(s) or runs action on draft.
                                actions:
                                  'p': generate pairings
                                  'g': add game
                                  'r': remove player
 D [<NAME/ID>]                  lists drafts and draft details
 F <NAME> [<NAME> ...]          get fafmats score between player and all players or list of player
"""


input_count = 0
while True:
    try:
        input_ = input('[{:03d}]> '.format(input_count))
        if not input_:
            continue
        flag = input_[0]
        input_string = input_[1:]
        input_string = input_string.strip()

        if flag == 'q':
            log.info('Quitting')
            break
        elif flag == 'h':
            log.info(HELP_MESSAGE)
        elif flag == 'p':
            handle_add_player(input_string, con)
        elif flag == 'P':
            handle_show_players(input_string, con)
        elif flag == 'g':
            handle_add_game(input_string, con)
        elif flag == 'G':
            handle_show_games(input_string, con)
        elif flag == 'H':
            handle_show_history(input_string, con)
        elif flag == 'd':
            handle_draft(input_string, con)
        elif flag == 'D':
            handle_show_drafts(input_string, con)
        elif flag == 'F':
            handle_show_score(input_string, con)
        else:
            log.error('Not a flag: "{}"'.format(flag))

    except (KeyboardInterrupt, EOFError):
        break
    except BaseException:
        log.error(format_exc())
    else:
        con.commit()  # only commit stuff that worked :-)
    finally:
        input_count += 1
