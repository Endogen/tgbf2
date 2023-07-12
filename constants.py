from pathlib import Path

DESCRIPTION = "Python Telegram Bot Framework 2"

# Folders
DIR_TEM = Path('templates')
DIR_PLG = Path('plg')
DIR_RES = Path('res')
DIR_CFG = Path('cfg')
DIR_LOG = Path('log')
DIR_DAT = Path('dat')
DIR_TMP = Path('tmp')

# Extensions
CFG_EXT = '.cfg'
DAT_EXT = '.db'

# Files
FILE_DAT = Path('global').with_suffix(DAT_EXT)
FILE_CFG = Path('global').with_suffix(CFG_EXT)

# Max Telegram message length
MAX_TG_MSG_LEN = 4096
