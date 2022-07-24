LOG_PATH = 'log'
DATABASE_PATH = 'data/data.db'

STARGING_ELO = 1000
EXPECTED_TENFOLD_ADVANTAGE = 400  # at 400 elo difference, the stronger opponent should score 10 times higher on average
K_FACTOR = 32

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
