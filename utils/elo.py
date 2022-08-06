from constants import EXPECTED_TENFOLD_ADVANTAGE, K_FACTOR, \
    RESULT_SCORE_DICT


def get_expected_elo_score(playerA_elo, playerB_elo):
    elo_difference = playerB_elo - playerA_elo
    return 1 / (1 + 10 ** (elo_difference / EXPECTED_TENFOLD_ADVANTAGE))


def get_elo_difference_from_result(playerA_elo, playerB_elo, result):
    playerA_score = RESULT_SCORE_DICT[result]
    playerA_expected_score = get_expected_elo_score(playerA_elo, playerB_elo)
    playerA_score_offset = playerA_score - playerA_expected_score
    elo_difference = K_FACTOR * playerA_score_offset
    return elo_difference


def get_draft_autopairing():
    pass
