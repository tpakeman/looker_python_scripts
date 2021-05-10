import logging
from datetime import datetime as dt
import os
def setup_log(name, logdir='logs'):
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    fname = os.path.join(logdir, f'{dt.now().date()}.log')
    log = logging.getLogger(name)
    logging.basicConfig(filename=fname, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return log
    
def cprint(text, choice=None, log=None, **kwargs):
    colours = {
                'HEADER': (log.info, '\033[95m'),
                'OKBLUE': (log.info, '\033[94m'),
                'OKGREEN': (log.info, '\033[92m'),
                'WARNING': (log.warn, '\033[93m'),
                'FAIL': (log.error, '\033[91m'),
                'END': (log.info, '\033[0m'),
                'BOLD': (log.info, '\033[1m'),
                'UNDERLINE': (log.info, '\033[4m')
            }
    if not choice:
        print(text, **kwargs)
        if log:
            log.info(text)
    elif choice not in colours.keys():
        raise ValueError(f"Colour must be in {colours.keys()}")
    else:
        print(f"{colours[choice][1]}{text}{colours['END'][1]}", **kwargs)
        if log:
            colours[choice][0](text)