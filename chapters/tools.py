"""
# Element tree (text) queries and tools relevant to factor rendering.
"""
import typing
from fault.text import document
from fault.text.types import Paragraph, Fragment

def select(types:set, nodes:typing.Iterable):
	"""
	# Retrieve the nodes whose element type identifier is in &types.
	"""
	for n in nodes:
		if n[0] in types:
			yield n

def first(types:set, nodes:typing.Iterable):
	"""
	# Get the first node with an element type in &types.
	"""
	for x in select(types, nodes):
		return x
	return None

def interpret_property_fragment(fragment):
	"""
	# Convert a fragment to a key-value pair. Inverse of &fragment_property.
	"""
	if fragment[0].startswith('literal/'):
		return (tuple(fragment.type.split('/')[2:]), fragment.data)
	elif fragment[0].startswith('reference/'):
		rt, rs, pi, *local = fragment.type.split('/')
		return ((pi, 'reference'), fragment.__class__(('/'.join([rt, rs] + local), fragment.data)))

def interpret_properties(items):
	"""
	# Get the set of unordered list based properties from the &nodes.

	# Returns the number of items present in the initial set found in &nodes,
	# and the set of sole paragraph fragments contained by each item.
	"""
	return list(map(interpret_property_fragment, (document.export(i[1][0][1]).sole for i in items)))

def get_properties(nodes):
	if nodes:
		typ, items, attr = nodes[0]
		if typ == 'set':
			try:
				return dict(interpret_properties(items))
			except (TypeError, ValueError):
				# Probably not a property set.
				pass

	return dict()

def itemize_fragment(pf:Fragment):
	"""
	# Construct single paragraph item node for populating a set or sequence node.
	"""
	return ('item', [('paragraph', Paragraph.of(pf), {})], {})

def fragment_property(item) -> Fragment:
	"""
	# Construct a fragment that can be directly serialized to represent the &item.
	"""
	k, v = item
	if isinstance(v, str):
		# Literal
		return Fragment(('literal/grave-accent/' + '/'.join(k), v))
	else:
		# Presumed reference.
		pi, pq = k
		assert pq == 'reference' # Non-string property was not reference qualified.
		rt, rs, *suffix = v.type.split('/')
		# Qualify the cast with &pi.
		reftype = [rt, rs, k[0]] + suffix
		return Fragment(('/'.join(reftype), v.data))
