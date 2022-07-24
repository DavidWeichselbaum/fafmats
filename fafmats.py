import os
import logging
import logging.config
from traceback import format_exc

import coloredlogs
import sqlite3 as sl

from constants import LOG_PATH, DATABASE_PATH, \
    RESULT_SCORE_DICT, WRONG_ORDER_RESULTS, INVERSE_RESULT_DICT
from utils.db_init import init_db
from utils.db_utils import add_player, add_match, update_elo, \
    get_player_id_by_name, get_player_elo, \
    get_players_table, get_matches_table
from utils.elo import get_elo_difference


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
