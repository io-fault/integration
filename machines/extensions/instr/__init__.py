"""
# LLVM utilities for extracting profile and coverage data.

# ! WARNING:
	# Currently does not provide information about expansion regions.
"""
__factor_domain__ = 'system'
__factor_type__ = 'extension'

requirements = (
	'python',
)

standards = {
	'c++': 'c++11',
}

from ...probes import libllvm
