from collections import defaultdict

import numpy as np
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform
from fastcluster import linkage

from utils.db_utils import get_fafmats_scores, get_player_name_by_id, get_n_wins
from constants import GENERATE_PLOTS


def get_fafmats_ordered_player_ids(player_ids, con):
    scores_list = []
    for i in range(len(player_ids)):
        player_id = player_ids[i]
        scores = get_fafmats_scores(player_id, player_ids, con)
        scores_list.append(scores)
    scores = np.array(scores_list)
    np.fill_diagonal(scores, 1)  # sometimes scores to player itself might not be 1 due to diviion by zero checks

    ordered_scores, result_order, result_linkage = compute_serial_matrix(scores, method='ward')
    ordered_player_ids = [player_ids[i] for i in result_order]

    if GENERATE_PLOTS:
        clusters = hierarchy.linkage(scores, method='ward')
        plot_dendrogram(clusters, player_ids, con)
        plot_scores(ordered_scores, ordered_player_ids, con)

    return ordered_player_ids


def get_draft_autopairing(draft_player_numbers, player_ids, con):
    ordered_player_ids = get_fafmats_ordered_player_ids(player_ids, con)

    draft_player_lists = []
    for draft_player_number in draft_player_numbers:
        draft_player_ids = ordered_player_ids[:draft_player_number]
        ordered_player_ids = ordered_player_ids[draft_player_number:]
        draft_player_lists.append(draft_player_ids)

    return draft_player_lists


def plot_scores(scores, player_ids, con):
    import matplotlib.pyplot as plt
    player_names = [get_player_name_by_id(player_id, con) for player_id in player_ids]
    plt.title('FAFMATS Scores')
    plt.pcolormesh(scores)
    plt.colorbar()
    plt.xticks(np.arange(len(player_names)) + 0.5, player_names, rotation=45)
    plt.yticks(np.arange(len(player_names)) + 0.5, player_names)
    plt.show()


def plot_dendrogram(clusters, player_ids, con):
    import matplotlib.pyplot as plt
    player_names = [get_player_name_by_id(player_id, con) for player_id in player_ids]
    plt.figure(figsize=(20, 6))
    plt.title('FAFMATS Tree')
    hierarchy.dendrogram(clusters, labels=player_names, orientation="top", leaf_font_size=9, leaf_rotation=360)
    plt.ylabel('Score Tree')
    plt.show()


def seriation(Z, N, cur_index):
    '''
        input:
            - Z is a hierarchical tree (dendrogram)
            - N is the number of points given to the clustering process
            - cur_index is the position in the tree for the recursive traversal
        output:
            - order implied by the hierarchical tree Z

        seriation computes the order implied by a hierarchical tree (dendrogram)
        from https://gmarti.gitlab.io/ml/2017/09/07/how-to-sort-distance-matrix.html
    '''
    if cur_index < N:
        return [cur_index]
    else:
        left = int(Z[cur_index-N, 0])
        right = int(Z[cur_index-N, 1])
        return (seriation(Z, N, left) + seriation(Z, N, right))


def compute_serial_matrix(dist_mat, method='ward'):
    '''
        input:
            - dist_mat is a distance matrix
            - method = ["ward", "single", "average", "complete"]
        output:
            - seriated_dist is the input dist_mat,
              but with re-ordered rows and columns
              according to the seriation, i.e. the
              order implied by the hierarchical tree
            - res_order is the order implied by
              the hierarchical tree
            - res_linkage is the hierarchical tree (dendrogram)

        compute_serial_matrix transforms a distance matrix into
        a sorted distance matrix according to the order implied
        by the hierarchical tree (dendrogram)
        from https://gmarti.gitlab.io/ml/2017/09/07/how-to-sort-distance-matrix.html
    '''
    N = len(dist_mat)
    flat_dist_mat = squareform(dist_mat, checks=False)
    res_linkage = linkage(flat_dist_mat, method=method, preserve_input=True)
    res_order = seriation(res_linkage, N, N + N-2)
    seriated_dist = np.zeros((N, N))
    a, b = np.triu_indices(N, k=1)
    seriated_dist[a, b] = dist_mat[[res_order[i] for i in a], [res_order[j] for j in b]]
    seriated_dist[b, a] = seriated_dist[a, b]

    return seriated_dist, res_order, res_linkage


def get_player_pairings(draft_id, round_, player_ids, con):
    if round_ == 1:
        pairings = get_random_player_pairing(player_ids, con)
    else:
        pairings = get_round_player_pairing_groups(draft_id, player_ids, round_, con)
        # TODO
    return pairings


def get_random_player_pairing(player_ids, con):
    ordered_player_ids = get_fafmats_ordered_player_ids(player_ids, con)
    ordered_player_ids_iterator = iter(ordered_player_ids)
    ordered_player_id_pairs = list(zip(ordered_player_ids_iterator, ordered_player_ids_iterator))
    if len(player_ids) % 2 != 0:
        ordered_player_id_pairs += [(ordered_player_ids[-1], )]  # add single player
    return ordered_player_id_pairs


def get_round_player_pairing_groups(draft_id, player_ids, round_, con):
    player_id_wins_dict = defaultdict(list)
    for player_id in player_ids:
        n_wins = get_n_wins(player_id, draft_id, con)
        player_id_wins_dict[player_id].append(n_wins)
    print(player_id_wins_dict)
