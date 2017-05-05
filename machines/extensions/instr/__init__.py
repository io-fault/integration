"""
# LLVM utilities for extracting profile and coverage data.

# ! WARNING:
	# Currently does not provide information about expansion regions.
"""
from ...probes import libllvm
from ....development.probes import libpython

standards = {
	'c++': 'c++11',
}

__factor_domain__ = 'system'
__factor_type__ = 'extension'
