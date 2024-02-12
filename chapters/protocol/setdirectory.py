"""
# Functions for extracting and integrating set based properties.
"""
from fault.text import types
from fault.text.io import structure_paragraph_element as ipara

def interpret_fragment(property_item:types.Fragment) -> tuple[tuple, str]:
	"""
	# Convert a fragment to a key-value pair.
	"""
	if property_item[0].startswith('literal/'):
		return (tuple(property_item.type.split('/')[2:]), property_item.data)
	elif property_item[0].startswith('reference/'):
		rt, rs, pi, *local = property_item.type.split('/')
		ref = property_item.__class__(('/'.join([rt, rs] + local), property_item.data))
		return ((pi, 'reference'), ref)
	else:
		return ((), property_item.data)

def interpret_set_items(items):
	"""
	# Get the set of unordered list based properties from the &items.

	# Returns the number of items present in the initial set found in &items,
	# and the set of sole paragraph fragments contained by each item.
	"""
	return map(interpret_fragment, (ipara(i[1][0]).sole for i in items))

def select(elements, *, index=0):
	"""
	# The interpreted property set items in &elements at &index.

	# [ Returns ]
	# An iterable of key-value pairs forming the property set
	# or an empty iterable if not a property set or no properties
	# were specified.
	"""
	if len(elements) <= index:
		return ()

	se = elements[index]
	if not se[0] == 'set':
		return ()

	items = iter(interpret_set_items(se[1]))

	# Iterate once to check for (control)`property-set` declaration.
	for kv in items:
		if kv != (('control',), 'property-set'):
			return ()
		break
	else:
		return ()

	return items

def formulate_fragment(item, *, isinstance=isinstance) -> types.Fragment:
	"""
	# Construct a &Fragment that represents the property in a &types.Paragraph instance.
	"""
	k, v = item # cast-literal or cast-reference pair.

	if isinstance(v, str):
		# Literal
		return types.Fragment(('literal/grave-accent/' + '/'.join(k), v))
	else:
		# Presumed reference.
		pi, pq = k
		assert pq == 'reference' # Non-string property was not reference qualified.
		rt, rs, *suffix = v.type.split('/')
		# Qualify the cast with &pi.
		reftype = [rt, rs, k[0]] + suffix
		return types.Fragment(('/'.join(reftype), v.data))
