import os
import logging
import logging.config
from traceback import format_exc

import coloredlogs
import sqlite3 as sl

from constants import LOG_PATH, DATABASE_PATH
from utils.db_init import init_db
from utils.cli_utils import handle_add_player, handle_add_match, \
    handle_show_players, handle_show_matches, handle_show_history, handle_show_drafts, \
    handle_draft


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
 p <NAME>                       add player
 P [<METHOD>]                   list players by method.
                                methods:
                                  'a/A': alphabetical
                                  'e/E': elo
                                  'd/D': date
 m <NAME> , <NAME> = <RESULT>   add 1v1 match between named players.
                                possible results: '2:0', '2:1', '1:2', '0:2', 'draw', 'forfeit'
 M [<NAME>]                     list matches, optionally filtered for player
 H <NAME>                       show elo history of player
 d <NAME> [<ACTION>]            start named draft(s) or runs action on draft.
                                actions:
                                  'p': generate pairings
                                  'r': remove player
                                  'm': add match
 D [<NAME>]                     lists drafts and draft details
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
        elif flag == 'm':
            handle_add_match(input_string, con)
        elif flag == 'M':
            handle_show_matches(input_string, con)
        elif flag == 'H':
            handle_show_history(input_string, con)
        elif flag == 'd':
            handle_draft(input_string, con)
        elif flag == 'D':
            handle_show_drafts(input_string, con)
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
