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

	# Returns the number of items present in the initial set found in &nodes,
	# and the set of sole paragraph fragments contained by each item.
	"""
	return map(interpret_fragment, (ipara(i[1][0]).sole for i in items))

def select(nodes, *, index=0):
	"""
	# Given the contents of an element, extract the properties from the set
	# located at the designated &index. Normally, properties are expected to be
	# presented at the beginning of some content and, therefore, &index defaults to `1`.

	# If the element at &index is not a `'set'`, or &nodes is an empty,
	# an empty iterator will be returned.

	# Error conditions produced during the production of a property set indicate
	# that it is not a property set at all and will cause an empty list to be returned.
	"""
	if nodes and nodes[index][0] == 'set':
		typ, items, attr = nodes[index]
		if typ == 'set':
			try:
				return interpret_set_items(items)
			except (TypeError, ValueError):
				# Probably not a property set.
				pass

	# Errors, empty list, and non-set cases.
	return iter(())

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
