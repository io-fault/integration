"""
# Testing and static analysis support.
"""

##
# Test types associated with their identifying prefix.
test_type_map = {
	'integration': 'i-',
	'unit': 'u-',
	'performance': 'p-',
	'explicit': 'x-',
}

# fault.vector restricted parameters dictionary.
test_type_set_control = {
	'--integration': ('set-add', 'integration', 'test-types'),
	'--unit': ('set-add', 'unit', 'test-types'),
	'--performance': ('set-add', 'performance', 'test-types'),
	'--explicit': ('set-add', 'explicit', 'test-types'),

	'-i': ('set-add', 'integration', 'test-types'),
	'-u': ('set-add', 'unit', 'test-types'),
	'-p': ('set-add', 'performance', 'test-types'),
	'-x': ('set-add', 'explicit', 'test-types'),

	'-I': ('set-discard', 'integration', 'test-types'),
	'-U': ('set-discard', 'unit', 'test-types'),
	'-P': ('set-discard', 'performance', 'test-types'),
	'-X': ('set-discard', 'explicit', 'test-types'),
}
