"""
# Factor graph primitives.

# Used by &.cc to order the target factors according to their dependencies.
"""
import collections

def traverse(directory, working, tree, inverse, node):
	"""
	# Invert the directed graph of dependencies from the node.
	"""

	deps = set(directory(node))

	if not deps:
		# No dependencies, add to working set and return.
		working.add(node)
		return
	elif node in tree:
		# It's already been traversed in a previous run.
		return

	# dependencies present, assign them inside the tree.
	tree[node] = deps

	for x in deps:
		# Note the factor as depending on &x and build
		# its tree.
		inverse[x].add(node)
		traverse(directory, working, tree, inverse, x)

def sequence(directory, nodes, defaultdict=collections.defaultdict, tuple=tuple):
	"""
	# Generator maintaining the state of the sequencing of a traversed dependency
	# graph. This generator emits factors as they are ready to be processed and receives
	# factors that have completed processing.

	# When a set of dependencies has been processed, they should be sent to the generator
	# as a collection; the generator identifies whether another set of modules can be
	# processed based on the completed set.

	# Completion is an abstract notion, &sequence has no requirements on the semantics of
	# completion and its effects; it merely communicates what can now be processed based
	# completion state.
	"""

	reqs = dict()
	tree = dict() # dependency tree; F -> {DF1, DF2, ..., DFN}
	inverse = defaultdict(set)
	working = set()
	empty = set()

	for node in nodes:
		traverse(directory, working, tree, inverse, node)

	new = working
	# Organize requirements by their factor type.
	for x, y in tree.items():
		cs = reqs[x] = defaultdict(set)
		for f in y:
			cs[f.type].add(f)

	yield None

	while working:
		completion = (yield tuple(new), reqs, {x: tuple(inverse[x]) for x in new if inverse[x]})
		new = set() # &completion triggers new additions to &working

		for node in (completion or ()):
			# completed.
			working.discard(node)

			for deps in inverse[node]:
				fd = tree.get(deps, empty)
				fd.discard(node)
				if not fd:
					# Add to both; new is the set reported to caller,
					# and working tracks when the graph has been fully sequenced.
					new.add(deps)
					working.add(deps)
