"""
# Factor Integration Control tool.

# Executes the module identified by the first argument.
"""
import importlib

from . import __name__ as project_package_name

def main(inv):
	module = importlib.import_module(project_package_name + '.' + inv.argv[0])
	del inv.argv[0:1]
	return module.main(inv)
