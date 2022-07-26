# paths
LOG_PATH = 'log'
SQLITE_SCRIPT_PATH = 'resources/fafmats.sql'
DATABASE_PATH = 'data/data.db'

# elo
STARGING_ELO = 1000
EXPECTED_TENFOLD_ADVANTAGE = 400  # at 400 elo difference, the stronger opponent should score 10 times higher on average
K_FACTOR = 32

# fafmats
FUN_FRIENDSHIP_RATIO = 0.5  # number in range [0,1]. 0 = fun only, 1 = friendship only

# results
RESULT_SCORE_DICT = {
    '2:0': 1,
    '2:1': 1,
    '1:2': 0,
    '0:2': 0,
    'draw': 0.5,
    'forfeit': 0.5}
WRONG_ORDER_RESULTS = ('0:2', '1:2')
INVERSE_RESULT_DICT = {
    '2:0': '0:2',
    '2:1': '1:2',
    '1:2': '2:1',
    '0:2': '2:0',
    'draw': 'draw',
    'forfeit': 'forfeit'}

# CLI
YES_STRINGS = ['y', 'Y', 'yes', 'Yes']
NO_STRINGS = ['n', 'N', 'no', 'No']
SORT_METHOD_STRINGS = ('a', 'A', 'e', 'E', 'd', 'D')
GENERATE_PLOTS = False
