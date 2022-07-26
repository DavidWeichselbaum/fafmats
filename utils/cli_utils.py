import re
import logging

from constants import RESULT_SCORE_DICT, WRONG_ORDER_RESULTS, INVERSE_RESULT_DICT, \
    YES_STRINGS, NO_STRINGS, SORT_METHOD_STRINGS
from utils.db_utils import add_player, add_match, update_elo, \
    get_player_id_by_name, get_player_elo, \
    get_players_table, get_matches_table, get_history_table, \
    add_draft, get_draft_id_by_name, add_player_to_draft, get_drafts_table
from utils.elo import get_elo_difference


log = logging.getLogger('cli_utils')


def handle_add_player(input_string, con):
    if not input_string:
        log.error('Name needed!')
        return

    while True:
        confirmation_string = input('    Add player "{}"? [y/n] > '.format(input_string))
        if confirmation_string in YES_STRINGS:
            add_player(input_string, con)
            log.info('Added player "{}"'.format(input_string))
            return
        elif confirmation_string in NO_STRINGS:
            return


def handle_show_players(input_string, con):
    if not input_string:
        input_string = 'a'
    elif input_string not in SORT_METHOD_STRINGS:
        log.error('Incorrect sort method')
        return

    player_table = get_players_table(con, input_string)
    log.info('\n' + player_table)


def handle_add_match(input_string, con):
    # make sure everything is a-okay
    input_strings = input_string.split('=')
    if len(input_strings) != 2:
        log.error('Need result!')
        return

    players_string = input_strings[0].strip()
    result_string = input_strings[1].strip()
    if result_string not in RESULT_SCORE_DICT:
        log.error('Result must be one of {}'.format(RESULT_SCORE_DICT.keys()))
        return

    player_strings = players_string.split(',')
    if len(player_strings) != 2:
        log.error('Need 2 players!')
        return
    playerA_name, playerB_name = player_strings[0].strip(), player_strings[1].strip()
    playerA_id = get_player_id_by_name(playerA_name, con)
    playerB_id = get_player_id_by_name(playerB_name, con)
    if playerA_id is None:
        log.error('Player "{}" does not exist. Too bad.'.format(playerA_name))
        return
    if playerB_id is None:
        log.error('Player "{}" does not exist. Lolnope.'.format(playerB_name))
        return
    if playerA_id == playerB_id:
        log.error('This is not solitaire, buddy!\nMinus 10 Elo :-)')
        return

    # make winner always playerA
    if result_string in WRONG_ORDER_RESULTS:
        result_string = INVERSE_RESULT_DICT[result_string]
        playerA_name, playerB_name, = playerB_name, playerA_name
        playerA_id, playerB_id, = playerB_id, playerA_id

    # get elo difference
    playerA_elo = get_player_elo(playerA_id, con)
    playerB_elo = get_player_elo(playerB_id, con)
    elo_difference = get_elo_difference(playerA_elo, playerB_elo, result_string)
    playerA_elo_new = playerA_elo + elo_difference
    playerB_elo_new = playerB_elo - elo_difference

    # ask for permission and save
    playerA_elo_sign = '+' if elo_difference >= 0 else '-'
    playerB_elo_sign = '+' if elo_difference <= 0 else '-'
    log.info('Results:\n{}: {:.0f} {} {:.0f} = {:.0f} elo\n{}: {:.0f} {} {:.0f} = {:.0f} elo".'.format(
        playerA_name, playerA_elo, playerA_elo_sign, abs(elo_difference), playerA_elo_new,
        playerB_name, playerB_elo, playerB_elo_sign, abs(elo_difference), playerB_elo_new))
    while True:
        confirmation_string = input('    Add Result? [Y/n] > ')
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
            return


def handle_show_matches(input_string, con):
    player_id = None
    if input_string:
        player_id = get_player_id_by_name(input_string, con)
        if player_id is None:
            log.error('Did not find that person!')
            return
    matches_table = get_matches_table(con, player_id)
    log.info('\n' + matches_table)


def handle_show_history(input_string, con):
    player_id = get_player_id_by_name(input_string, con)
    if player_id is None:
        log.error('Did not find that person!')
        return
    history_table = get_history_table(con, player_id)
    log.info('\n' + history_table)


def handle_draft(input_string, con):
    method = re.findall(' ([A-z])$', input_string)
    if not method:
        handle_add_draft(input_string, con)

    draft_name = input_string[:-2]
    draft_id = get_draft_id_by_name(draft_name, con)
    if method == 'p':
        handle_draft_pairings()


def handle_add_draft(draft_name, con):
    draft_id = get_draft_id_by_name(draft_name, con)
    if draft_id is not None:
        log.error('Name already exists!')
        return

    # add players
    log.info('Add Players, stop with empty input.')
    player_ids, player_names = [], []
    while True:
        player_name = input('    player #{} > '.format(len(player_ids) + 1))
        if player_name == '':
            break

        player_id = get_player_id_by_name(player_name, con)
        if player_id is None:
            log.warning('Name not found.')
            continue
        elif player_id in player_ids:
            log.warning('No, you can\'t play twice for double elo.')
            continue
        else:
            player_ids.append(player_id)
            player_names.append(player_name)

    if len(player_ids) < 2:
        log.error('Can\'t have a draft alone now, can you?')
        return

    # separte drafts if wanted
    log.info('Start multi-table draft? Divide {} players into tables or leave emtpy.'.format(len(player_ids)))
    draft_names, draft_player_numbers, draft_player_id_lists, draft_player_names_lists = [], [], [], []
    players_left = len(player_names)
    while True:
        player_number_string = input('    number players in draft "{}-{}" ({} left)> '.format(
            draft_name, len(draft_names) + 1, players_left))

        if player_number_string == '':
            draft_names.append(draft_name)
            draft_player_numbers.append(len(player_ids))
            break

        try:
            player_number = int(player_number_string)
        except ValueError:
            log.warning('Do you know what numbers are?')
            continue

        draft_names.append('{}-{}'.format(draft_name, len(draft_names) + 1))
        draft_player_numbers.append(player_number)

        players_left -= player_number
        if players_left == 0:
            break
        elif players_left < 2:
            log.warning('I\'m sure we can do better in dividing them up, hm?')
            return

    # automatically pair if wanted
    if len(draft_names) > 1:
        autopair = True
        while True:
            confirmation_string = input('Autopair? [Y/n] > ')
            if confirmation_string in YES_STRINGS + ['']:
                autopair = True
                break
            elif confirmation_string in NO_STRINGS:
                autopair = False
                break

        if autopair:
            pass
        else:
            pass

    else:
        draft_player_id_lists.append(player_ids)
        draft_player_names_lists.append(player_names)

    # start draft(s)
    for draft_name, draft_player_names, draft_player_ids in \
            zip(draft_names, draft_player_names_lists, draft_player_id_lists):

        while True:
            confirmation_string = input('Add draft "{}" with players {}? [y/n] > '.format(
                draft_name, ', '.join(draft_player_names)))
            if confirmation_string in YES_STRINGS:
                break
            elif confirmation_string in NO_STRINGS:
                return

        draft_id = add_draft(draft_name, con)
        for player_id in player_ids:
            add_player_to_draft(player_id, draft_id, con)

        log.info('Added draft "{}" with players: {}'.format(draft_name, ', '.join(player_names)))


def handle_show_drafts(input_string, con):
    draft_id, player_id = None, None

    if input_string:
        draft_id = get_draft_id_by_name(input_string, con)
        drafts_table = get_drafts_table(con, draft_id=draft_id)
    elif input_string and not draft_id:
        player_id = get_player_id_by_name(input_string, con)
        drafts_table = get_drafts_table(con, player_id=player_id)
    elif input_string and not draft_id and not player_id:
        log.error('"{}" is neither a draft nor a player!')
        return
    else:
        drafts_table = get_drafts_table(con)

    log.info('\n' + drafts_table)
