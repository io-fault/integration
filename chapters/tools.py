"""
Various utilities supporting processing.
"""

def strip_notation_prefix(lines, prefix='# '):
	"""
	# Remove the comment notation prefix from a string.
	"""
	pl = len(prefix)
	return [
		(('\t'*(xl-len(y))) + y[pl:] if y[:pl] == prefix else x)
		for xl, x, y in [
			(len(z), z, z.lstrip('\t'))
			for z in lines
		]
	]
