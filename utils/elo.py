from constants import EXPECTED_TENFOLD_ADVANTAGE, K_FACTOR, \
    RESULT_SCORE_DICT, FUN_FRIENDSHIP_RATIO


def get_expected_elo_score(playerA_elo, playerB_elo):
    elo_difference = playerB_elo - playerA_elo
    return 1 / (1 + 10 ** (elo_difference / EXPECTED_TENFOLD_ADVANTAGE))


def get_elo_difference_from_result(playerA_elo, playerB_elo, result):
    playerA_score = RESULT_SCORE_DICT[result]
    playerA_expected_score = get_expected_elo_score(playerA_elo, playerB_elo)
    playerA_score_offset = playerA_score - playerA_expected_score
    elo_difference = K_FACTOR * playerA_score_offset
    return elo_difference


def get_elo_score(elo_difference, min_elo_difference, max_elo_difference):
    if max_elo_difference - min_elo_difference == 0:
        return 0.5
    else:
        return 1 - (elo_difference - min_elo_difference) / (max_elo_difference - min_elo_difference)


def get_encounter_score(n_encounters, min_encounters, max_encounters):
    if max_encounters - min_encounters == 0:
        return 0.5
    else:
        return 1 - (n_encounters - min_encounters) / (max_encounters - min_encounters)


def get_fafmats_score(elo_score, encounters_score):
    return elo_score * FUN_FRIENDSHIP_RATIO + encounters_score * (1-FUN_FRIENDSHIP_RATIO)


def calculate_fafmats_scores(elo_differences, n_encounters_list):
    min_elo_difference = min(elo_differences)
    max_elo_difference = max(elo_differences)
    min_encounters = min(n_encounters_list)
    max_encounters = max(n_encounters_list)

    opponent_scores = []
    for elo_difference, n_encounters in zip(elo_differences, n_encounters_list):
        elo_score = get_elo_score(elo_difference, min_elo_difference, max_elo_difference)
        encounters_score = get_encounter_score(n_encounters, min_encounters, max_encounters)

        fafmats_score = get_fafmats_score(elo_score, encounters_score)
        opponent_scores.append(fafmats_score)

    return opponent_scores
