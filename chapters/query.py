"""
# Query context for navigating chapter elements.
"""
from fault.route.query import Context, Cursor, InvalidPath

def identify(title, element):
	"""
	# Identification function for chapter elements providing
	# shortcuts for directories and sequences.
	"""
	if element[0] in ('admonition', 'syntax'):
		if element[2]['type'] == title:
			yield element
	else:
		if element[2]['identifier'] == title:
			yield element

# Path expression context for navigating chapter element trees.
context = Context(
	{
		'paragraph',
		'syntax',
		'line',

		'chapter',
		'section',
		'admonition',
		'directory',
		'sequence',
		'set',

		'item',
		'key',
		'value',
	},
	{
		'p': 'paragraph',
		'i': 'item',
		'd': 'directory',
		's': 'sequence',
		'S': 'section',
		'C': 'chapter',
	},
	identify = identify,
)

def navigate(chapter) -> Cursor:
	"""
	# Construct a &Cursor instance using the given &chapter element
	# with the configured expression &context.
	"""
	return Cursor(context, [chapter])
