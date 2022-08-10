import re
import logging

from tabulate import tabulate

from constants import RESULT_SCORE_DICT, WRONG_ORDER_RESULTS, INVERSE_RESULT_DICT, \
    YES_STRINGS, NO_STRINGS, SORT_METHOD_STRINGS
from utils.db_utils import add_player, add_game, update_elo, \
    get_player_id_by_name, get_player_elo, \
    get_players_table, get_games_table, get_history_table, \
    add_draft, get_draft_id_by_name, add_player_to_draft, \
    get_drafts_table, get_draft_table, \
    get_all_player_ids, get_player_name_by_id, get_n_encounters, \
    get_elo_difference, get_fafmats_scores, \
    get_round_by_draft_id, get_active_draft_players, \
    add_player_draft_pairing, get_draft_pairings_by_draft_id, \
    get_draft_suspensions_by_draft_id, get_draft_name_by_id, \
    delete_pairings_by_draft_id, delete_suspensions_by_draft_id, \
    add_game_id_to_draft
from utils.elo import get_elo_difference_from_result
from utils.pairing import get_draft_autopairing, get_player_pairings


log = logging.getLogger('cli_utils')


def get_confimation(question='Do the thing?', default=None):
    if default is True:
        default_string = '[Y/n]'
        yes_strings = YES_STRINGS + ['']
        no_strings = NO_STRINGS
    elif default is False:
        default_string = '[y/N]'
        yes_strings = YES_STRINGS
        no_strings = NO_STRINGS + ['']
    else:
        default_string = '[y/n]'
        yes_strings = YES_STRINGS
        no_strings = NO_STRINGS

    log.info(question)

    while True:
        confirmation_string = input('{} {} > '.format(question, default_string))
        if confirmation_string in yes_strings:
            return True
        elif confirmation_string in no_strings:
            return False
        else:
            return None


def handle_add_player(input_string, con):
    names = input_string.split()
    if len(names) != 2:
        log.error('First name and last name needed!')
        return

    first_name, last_name = names[0], names[1]
    if ' ' in first_name or ' ' in last_name:
        log.error('No whitespaces allowed in names!')
        return

    confirmation = get_confimation('    Add player "{}"?'.format(input_string))
    if confirmation:
        add_player(first_name, last_name, con)
        log.info('Added player "{}"'.format(input_string))


def handle_show_players(input_string, con):
    if not input_string:
        input_string = 'a'
    elif input_string not in SORT_METHOD_STRINGS:
        log.error('Incorrect sort method')
        return

    player_table = get_players_table(con, input_string)
    log.info('\n' + player_table)


def handle_add_game(input_string, con):
    # make sure everything is a-okay
    input_strings = input_string.split()
    if len(input_strings) != 3:
        log.error('Need 2 names and result!')
        return

    playerA_name = input_strings[0]
    playerB_name = input_strings[1]
    result_string = input_strings[2]
    if result_string not in RESULT_SCORE_DICT:
        log.error('Result must be one of {}'.format(RESULT_SCORE_DICT.keys()))
        return

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
    elo_difference = get_elo_difference_from_result(playerA_elo, playerB_elo, result_string)
    playerA_elo_new = playerA_elo + elo_difference
    playerB_elo_new = playerB_elo - elo_difference

    # ask for permission and save
    playerA_elo_sign = '+' if elo_difference >= 0 else '-'
    playerB_elo_sign = '+' if elo_difference <= 0 else '-'
    log.info('Results:\n{}: {:.0f} {} {:.0f} = {:.0f} elo\n{}: {:.0f} {} {:.0f} = {:.0f} elo".'.format(
        playerA_name, playerA_elo, playerA_elo_sign, abs(elo_difference), playerA_elo_new,
        playerB_name, playerB_elo, playerB_elo_sign, abs(elo_difference), playerB_elo_new))

    confirmation = get_confimation('    Add result?', default=True)
    if confirmation:
        log.info('Accepted Result')
        game_id = add_game(playerA_id, playerB_id, result_string, con)
        update_elo(playerA_id, elo_difference, game_id, con)
        update_elo(playerB_id, - elo_difference, game_id, con)
        return game_id
    else:
        log.info('Rejected Result')


def handle_show_games(input_string, con):
    player_id = None
    if input_string:
        player_id = get_player_id_by_name(input_string, con)
        if player_id is None:
            log.error('Could not find that person!')
            return
    games_table = get_games_table(con, player_id)
    log.info('\n' + games_table)


def handle_show_history(input_string, con):
    player_id = get_player_id_by_name(input_string, con)
    if player_id is None:
        log.error('Could not find that person!')
        return
    history_table = get_history_table(con, player_id)
    log.info('\n' + history_table)


def handle_draft(input_string, con):
    method_games = re.findall(' ([A-z])$', input_string)
    if not method_games:
        handle_add_draft(input_string, con)
        return

    draft_name = input_string[:-2]
    if draft_name.isdigit():
        draft_id = int(draft_name)
    else:
        draft_id = get_draft_id_by_name(draft_name, con)

    if draft_id is None:
        log.error('Could not find draft "{}"'.format(draft_name))

    method = method_games[0]
    if method == 'p':
        handle_draft_pairings(draft_id, con)
    if method == 'P':
        handle_show_draft_pairings(draft_id, con)
    elif method == 'g':
        handle_draft_game(draft_id, con)
    # elif method == 'r':
    #     handle_remove_draft_player(draft_id, con)
    # else:
    #     log.warning('Method "{}" does not exist'.format(method))


def handle_draft_game(draft_id, con):
    draft_name = get_draft_name_by_id(draft_id, con)
    draft_round = get_round_by_draft_id(draft_id, con)
    match_adding_string = input('    Add game to draft "{}" round {} > '.format(draft_name, draft_round))

    game_id = handle_add_game(match_adding_string, con)
    if game_id is None:
        return

    add_game_id_to_draft(game_id, draft_id, draft_round, con)


def handle_add_draft_players(con):
    log.info('Add Players, stop with empty input.')
    player_ids = []
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
    return player_ids


def handle_draft_separation(draft_name, player_ids, con):
    log.info('Start multi-table draft? Divide {} players into tables or leave emtpy.'.format(len(player_ids)))
    draft_names, draft_player_numbers = [], []
    players_left = len(player_ids)
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
            raise ValueError

    return draft_names, draft_player_numbers


def handle_table_pairing(draft_player_numbers, player_ids, con):
    confirmation = get_confimation('Autopair?', default=True)
    if confirmation is True:
        return get_draft_autopairing(draft_player_numbers, player_ids, con)


def handle_add_draft_confirmation(draft_name, draft_names, draft_player_id_lists, con):
    for draft_name, draft_player_ids in zip(draft_names, draft_player_id_lists):
        draft_player_names = [get_player_name_by_id(player_id, con) for player_id in draft_player_ids]

        confirmation = get_confimation('Add draft "{}" with players {}?'.format(
            draft_name, ', '.join(draft_player_names)))
        if confirmation is False:
            log.warning('Aborted draft "{}"'.format(draft_name))
            return

    for draft_name, draft_player_ids in zip(draft_names, draft_player_id_lists):
        draft_player_names = [get_player_name_by_id(player_id, con) for player_id in draft_player_ids]

        draft_id = add_draft(draft_name, con)
        for player_id in draft_player_ids:
            add_player_to_draft(player_id, draft_id, con)

        log.info('Added draft "{}" with players: {}'.format(draft_name, ', '.join(draft_player_names)))


def handle_add_draft(draft_name, con):
    draft_id = get_draft_id_by_name(draft_name, con)
    if draft_id is not None:
        log.error('Name already exists!')
        return
    if ' ' in draft_name:
        log.error('No whitespaces allowed in names!')
        return

    player_ids = handle_add_draft_players(con)

    if len(player_ids) < 2:
        log.error('Can\'t have a draft alone now, can you?')
        return

    draft_names, draft_player_numbers = handle_draft_separation(draft_name, player_ids, con)

    if len(draft_names) == 1:
        draft_player_id_lists = [player_ids]
    else:
        draft_player_id_lists = handle_table_pairing(draft_player_numbers, player_ids, con)

    print(draft_name, draft_names, draft_player_id_lists, con)
    handle_add_draft_confirmation(draft_name, draft_names, draft_player_id_lists, con)


def handle_show_drafts(input_string, con):
    draft_id, player_id = None, None

    if not input_string:
        drafts_table = get_drafts_table(con)
    else:
        if input_string.isdigit():
            draft_id = int(input_string)
        else:
            draft_id = get_draft_id_by_name(input_string, con)
        player_id = get_player_id_by_name(input_string, con)

    if input_string and draft_id is None and player_id is None:
        log.error('"{}" is neither a draft nor a player!'.format(input_string))
        return
    elif draft_id is not None:
        log.info('Showing draft "{}"'.format(input_string))
        drafts_table = get_draft_table(draft_id, con)
    elif player_id is not None:
        log.info('Showing drafts including player "{}"'.format(input_string))
        drafts_table = get_drafts_table(con, player_id=player_id)

    log.info('\n' + drafts_table)


def handle_show_score(input_string, con):
    player_names = input_string.split()
    if not player_names:
        log.error('Need players!')
        return

    player_ids = []
    for player_name in player_names:
        player_id = get_player_id_by_name(player_name, con)
        if player_id is None:
            log.error('Player "{}" does not exist!'.format(player_name))
            return
        player_ids.append(player_id)

    player_id = player_ids.pop(0)
    opponent_ids = player_ids

    if not opponent_ids:  # chose all players if no others given
        opponent_ids = get_all_player_ids(con)
        opponent_ids.remove(player_id)

    opponent_scores = get_fafmats_scores(player_id, opponent_ids, con)

    table_data = []
    for opponent_id, score in zip(opponent_ids, opponent_scores):
        opponent_name = get_player_name_by_id(opponent_id, con)
        score_percent = score * 100
        elo_difference = get_elo_difference(player_id, opponent_id, con)
        n_encounters = get_n_encounters(player_id, opponent_id, con)
        table_data.append((opponent_name, score_percent, elo_difference, n_encounters))

    table_data.sort(key=lambda x: x[1])
    table = tabulate(table_data, headers=('opponent', 'score', 'elo difference', 'encounters'), floatfmt='.0f')
    log.info('\n' + table)


def handle_draft_pairings(draft_id, con):
    draft_round = get_round_by_draft_id(draft_id, con)
    player_pairings = get_draft_pairings_by_draft_id(draft_id, draft_round, con)
    if player_pairings:
        confirmation = get_confimation('Pairings exist already! Overwrite?', default=False)
        if confirmation is not True:
            return
        else:
            delete_pairings_by_draft_id(draft_id, draft_round, con)
            delete_suspensions_by_draft_id(draft_id, draft_round, con)

    log.info('Generating pairings for round {}'.format(draft_round))

    active_players = get_active_draft_players(draft_id, con)
    player_pairings = get_player_pairings(draft_id, draft_round, active_players, con)
    add_player_draft_pairing(player_pairings, draft_id, draft_round, con)
    handle_show_draft_pairings(draft_id, con)


def handle_show_draft_pairings(draft_id, con):
    draft_round = get_round_by_draft_id(draft_id, con)
    draft_name = get_draft_name_by_id(draft_id, con)
    log.info('Pairings for draft "{}" round {}'.format(draft_name, draft_round))

    player_pairings = get_draft_pairings_by_draft_id(draft_id, draft_round, con)
    for player_ids in player_pairings:
        player_A_name = get_player_name_by_id(player_ids[0], con)
        player_B_name = get_player_name_by_id(player_ids[1], con)
        log.info('Game:       {:<15} vs {:>15}'.format(player_A_name, player_B_name))

    suspended_players = get_draft_suspensions_by_draft_id(draft_id, draft_round, con)
    for suspended_player_id in suspended_players:
        player_name = get_player_name_by_id(suspended_player_id, con)
        log.info('Suspension: {}'.format(player_name))
