import sys
import os
import os.path

if __name__ == '__main__':
	exedir = os.path.dirname(__file__)
	os.execl(os.path.join(exedir, '__pycache__', 'factor', 'pf.lnk'), *sys.argv)
