"""
# Query context for navigating chapter nodes.
"""
from fault.route.query import Context, Cursor, InvalidPath

def identify(title, node):
	"""
	# Identification function for chapter nodes providing
	# shortcuts for directories and sequences.
	"""
	if node[0] in ('admonition', 'syntax'):
		if node[2]['type'] == title:
			yield node
	else:
		if node[2]['identifier'] == title:
			yield node

# Path expression context for navigation chapter node trees.
context = Context(
	{
		'paragraph',
		'syntax',
		'line',

		'chapter',
		'section',
		'admonition',
		'dictionary',
		'sequence',
		'set',

		'item',
		'key',
		'value',
	},
	{
		'p': 'paragraph',
		'i': 'item',
		'd': 'dictionary',
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
