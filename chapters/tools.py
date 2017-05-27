"""
# Various utilities supporting processing.
"""

def remove_common_indentation(lines):
	"""
	# Remove the leading indentation level from the given lines.
	"""

	# first non-empty line is used to identify
	# the indentation level of the entire string.
	for fl in lines:
		if fl.strip():
			break

	if fl.startswith('\t'):
		indentation = len(fl) - len(fl.lstrip('\t'))
		return [x[indentation:] for x in lines]
	else:
		# presume no indentation and likely single line
		return lines

def strip_notation_prefix(lines, prefix='# '):
	"""
	# Remove the comment notation prefix from a sequence of lines.
	"""

	pl = len(prefix)
	return [
		(('\t'*(xl-len(y))) + y[pl:] if y[:pl] == prefix else x)
		for xl, x, y in [
			(len(z), z, z.lstrip('\t'))
			for z in lines
		]
	]

def normalize_documentation(lines, prefix='# '):
	"""
	# Remove the leading indentation level from the given lines.
	"""

	# first non-empty line is used to identify
	# the indentation level of the entire string.
	for fl in lines:
		if fl.strip():
			break

	if fl.startswith('\t'):
		indentation = len(fl) - len(fl.lstrip('\t'))
		plines = strip_notation_prefix([x[indentation:] for x in lines], prefix=prefix)
		return plines
	else:
		# assume no indentation and likely single line
		plines = strip_notation_prefix(lines, prefix=prefix)
		return plines

def construct_corpus_map(directory, index):
	import itertools
	from ..xml import library as libxml
	content = libxml.element('map',
		itertools.chain.from_iterable(
			libxml.element('item',
				libxml.escape_element_string(str(r)),
				('key', k)
			)
			for k, r in index.items()
		),
		('dictionary', directory),
		('xmlns', 'http://fault.io/xml/filesystem#index'),
	)

	return b''.join(content)
