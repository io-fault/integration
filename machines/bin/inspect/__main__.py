import sys
import os
import os.path

exedir = os.path.dirname(__file__)
os.execl(os.path.join(exedir, '__pycache__', 'host', 'optimal', 'factor'), *sys.argv)
