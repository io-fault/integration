##
# .bin.init - initialize a new project package
##
import os.path

SETUP = """
#!/usr/bin/env python
##
# setup.py - .release.xdistutils
##
import sys

# distutils data is kept in `{project}.release.xdistutils`
sys.path.insert(0, '')

sys.dont_write_bytecode = True
import {project}.release.xdistutils as dist
defaults = dist.standard_setup_keywords()
sys.dont_write_bytecode = False

if __name__ == '__main__':
	try:
		from setuptools import setup
	except ImportError:
		from distutils.core import setup
	setup(**defaults)
"""

def ignore(dir, names):
	return [
		x for x in names
		if x.endswith('.pyc') or x.endswith('.pyo')
	]

def main(project_name):
	from .. import skeleton
	import shutil
	root = os.path.dirname(skeleton.__file__)
	root = os.path.realpath(root)
	shutil.copytree(root, project_name, ignore = ignore)
	with open('setup.py', 'a') as f:
		f.write(SETUP.format(project = project_name).strip())

if __name__ == '__main__':
	import sys
	main(sys.argv[1])
