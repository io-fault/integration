"""
# AST manipulations for injecting coverage counters and profile timers into Python modules.
"""
import ast
import builtins
import functools

from . import module
from . import source

BranchNodes = (
	ast.BoolOp,
	ast.IfExp,
)

expression_mapping = {
	ast.withitem: 'context_expr',
	ast.comprehension: 'value',
}

def visit_expression(node, parent, field, index, isinstance=isinstance):
	"""
	# Visit the node in a statement. Keyword defaults, expressions, statements.
	"""

	if isinstance(node, ast.withitem):
		yield from visit_expression(node.context_expr, node, 'context_expr', None)
		return
	elif isinstance(node, (ast.keyword, ast.Starred, ast.comprehension)):
		# Instrument the inside of the comprehension.
		yield from visit_expression(node.value, node, 'value', None)
		return
	elif isinstance(node, ast.arguments):
		# Only need keywords.
		for i, v in source.sequence_nodes(node.kw_defaults):
			yield from visit_expression(v, node, 'kw_defaults', i)
		return
	elif isinstance(node, (ast.Expr, ast.Return, ast.Assign, ast.AugAssign)):
		yield node.value, node, 'value', None
	else:
		# Count the expression as a whole.
		yield node, parent, field, index

	branches = set(x for x in source.bottom(node) if isinstance(x[0], BranchNodes))
	for x in branches:
		if isinstance(x[0], ast.BoolOp):
			for i, v in zip(range(len(x[0].values)), x[0].values):
				if isinstance(v, ast.AST):
					yield (v, x[0], 'values', i)
		elif isinstance(x[0], ast.IfExp):
			for y in source.shallow(x[0]):
				yield y
		else:
			pass # Never

def visit_container(nodes, parent, field, isinstance=isinstance):
	for index, stmt in nodes:
		if isinstance(stmt, ast.For):
			yield from visit_expression(stmt.iter, stmt, 'iter', None)
			yield from visit_container(source.sequence_nodes(stmt.body), stmt, 'body')
		elif hasattr(stmt, 'body'):
			yield from visit(stmt, parent, field, index)
		elif isinstance(stmt, ast.arguments):
			# Only need keywords.
			for i, v in source.sequence_nodes(stmt.kw_defaults):
				yield from visit_expression(v, stmt, 'kw_defaults', i)
		elif isinstance(stmt, ast.Expr) and stmt.col_offset == -1:
			# Likely docstring.
			pass
		elif isinstance(stmt, (ast.Name,)):
			pass
		elif isinstance(stmt, (ast.Break, ast.Continue)):
			yield (stmt, parent, field, index)
		else:
			yield from visit_expression(stmt, parent, field, index)

def visit(node, parent=None, field=None, index=None, sequencing=source.sequence_nodes):
	"""
	# Identify nodes that should be instrumented for coverage and profiling.
	"""
	for subfield, subnode in ast.iter_fields(node):
		if isinstance(subnode, ast.AST):
			yield from visit_expression(subnode, node, subfield, None)
		elif isinstance(subnode, list):
			yield from visit_container(sequencing(subnode), node, subfield)
		else:
			pass

coverage_module_context = """
if True:
	import collections as _fi_cl
	import atexit as _fi_ae
	import functools as _fi_ft
	import os as _fi_os

	_fi_counters__ = _fi_cl.Counter()
	_fi_identity = _fi_os.environ.get('METRICS_IDENTITY') or ''

	def _fi_record(counters=_fi_counters__, origin=_fi_identity, Retry=32):
		import sys, os, collections

		if 'PROCESS_IDENTITY' in os.environ:
			pid = os.environ['PROCESS_IDENTITY']
		else:
			pid = str(os.getpid())

		if 'METRICS_CAPTURE' in os.environ:
			# If capture is defined, qualify with the module name.
			# /../metrics/{pid}/{module}/{project}/{factor}/{test}/.fault-syntax-counters
			path = os.environ['METRICS_CAPTURE']
			path += '/coverage'
			path += '/' + pid
			path += '/' + __name__
		else:
			try:
				if __metrics_trap__ is None:
					# No destination.
					return
			except NameError:
				return

			# /../metrics/coverage/{pid}/{project}/{factor}/{test}/.fault-syntax-counters
			# Resolve __metrics_trap__ global at exit in order to allow the runtime
			# to designate it given compile time absence.
			path = __metrics_trap__
			path += '/coverage'
			path += '/' + pid

		path += '/' + os.environ.get('METRICS_IDENTITY', '.fault-python')
		path += '/.fault-syntax-counters'
		for x in range(Retry):
			try:
				os.makedirs(path)
			except FileExistsError:
				pass
			else:
				break

		# Vectorize the counters.
		events = collections.defaultdict(list)
		occurrences = collections.defaultdict(list)
		for (fp, area), v in counters.items():
			events[fp].append(area)
			occurrences[fp].append(v)

		# Sequence the sources for an index.
		# The contents of the vectors will be emitted according to this list.
		sources = list(events.keys())
		sources.sort()

		# Index designating sources and the number of counters.
		# For Python, this will normally (always) be a single line.
		# Append as PROCESS_IDENTITY may be intentionally redundant.
		with open(path + '/sources', 'a') as f:
			f.writelines(['%d %s\\n' %(len(events[x]), x) for x in sources])

		with open(path + '/areas', 'a') as f:
			for x in sources:
				f.writelines(['%d %d %d %d\\n' % k for k in events[x]])

		with open(path + '/counts', 'a') as f:
			for x in sources:
				f.writelines(['%d\\n' %(c,) for c in occurrences[x]])

	_fi_ae.register(_fi_record)

	try:
		_FI_INCREMENT__ = _fi_ft.partial(_fi_cl._count_elements, _fi_counters__)
	except:
		_FI_INCREMENT__ = _fi_counters__.update

	def _FI_COUNT__(area, rob, F=__file__, C=_FI_INCREMENT__):
		C(((F, area),))
		return rob

	# Limit names left in the module globals.
	del _fi_os, _fi_ft, _fi_cl, _fi_ae, _fi_record, _fi_identity
""".strip() + '\n'

count_boolop_expression = "(_FI_INCREMENT__(((__file__, %r),)) or INSTRUMENTATION_ERROR)"
count_call_expression = "_FI_COUNT__(%r,None)"

# Seeks the pass for the replacement point.
profile_transaction = """
if True:
	try:
		_FI_ENTER__(%r)
		pass
	finally:
		_FI_EXIT__(%r)
"""

profile_pause = """
if True:
	try:
		_FI_SUSPEND__(%r)
		pass
	finally:
		_FI_CONTINUE__(%r)
"""

def construct_call_increment(node, area, path='/dev/null', lineno=1):
	s = count_call_expression % (area,)
	p = ast.parse(s, path)
	k = p.body[0]
	for x in ast.walk(k):
		source.node_set_address(x, (-lineno, -1))

	update = functools.partial(k.value.args.__setitem__, -1)
	return k, update

def construct_boolop_increment(node, area, path='/dev/null', lineno=1):
	s = count_boolop_expression % (area,)
	p = ast.parse(s, path)
	expr = p.body[0]
	for x in ast.walk(expr):
		source.node_set_address(x, (-lineno, -1))

	update = functools.partial(expr.value.values.__setitem__, 1)
	return expr, update

def construct_profile_trap(identifier, container, nodes, path='/dev/null', lineno=1):
	src = profile %(identifier,identifier)
	tree = ast.parse(src, path)
	trap = tree.body[0].body[0]

	trap.body[1:1] = nodes
	assert isinstance(trap.body[-1], ast.Pass)
	del trap.body[-1]

	return trap

def construct_initialization_nodes(path="/dev/null"):
	"""
	# Construct instrumentation initialization nodes for injection into an &ast.Module body.
	"""
	nodes = ast.parse(coverage_module_context, path)
	for x in ast.walk(nodes):
		source.node_set_address(x, (-1, -1))

	return nodes

def instrument(record, path, noded, address):
	"""
	# Adjust the AST so that &node will record its execution.
	"""

	# Counter injection node.
	node, parent, field, index = noded

	if isinstance(node, ast.Pass):
		note, update = construct_call_increment(node, address)
		getattr(parent, field)[index] = note
		record.add(address)
	elif isinstance(node, ast.expr):
		note, update = construct_boolop_increment(node, address, path=path)
		update(node)
		if index is None:
			setattr(parent, field, note.value)
		else:
			getattr(parent, field)[index] = note.value
		record.add(address)
	elif isinstance(node, (ast.arguments, ast.arg)):
		pass
	else:
		note, update = construct_call_increment(node, address)
		if index is not None:
			position=(0 if isinstance(node, source.InterruptNodes) else 1)
			getattr(parent, field).insert(index+position, note)
			record.add(address)
		else:
			assert False
			pass # never

	return node

def delineate(noded):
	node = noded[0]
	if hasattr(node, '_f_context'):
		area = node._f_context[0][0:2] + node._f_area[2:]
	else:
		area = getattr(node, '_f_area', None)

	return area

def apply(record, path, noded):
	node = noded[0]
	if hasattr(node, '_f_context'):
		area = node._f_context[0][0:2] + node._f_area[2:]
	else:
		area = node._f_area

	return instrument(record, path, noded, area)

def compile(factor, source, path, constants,
		parse=source.parse,
		hash=module.hash_syntax,
		filter=visit,
		record=None,
	):
	"""
	# Compile Python source of a module into an instrumented &types.CodeObject
	"""
	srclines, tree, nodes = parse(source, path, filter=visit)

	for noded in nodes:
		if not hasattr(noded[0], '_f_area'):
			continue
		if isinstance(noded[0], (ast.expr_context, ast.slice)):
			continue

		apply(record, path, noded)

	# Insert profiling or coverage header before constants.
	tree.body[0:0] = construct_initialization_nodes().body

	# Add hash and canonical factor path.
	constants.extend([
		('__factor__', factor),
		('__source_hash__', hash(source)),
	])
	return module.inject(tree, constants)

if __name__ == '__main__':
	from . import bytecode
	import sys
	import os
	out, src = sys.argv[1:]

	st = os.stat(src)
	with open(src) as f:
		co = compile(None, f.read(), src, (), filter=visit)

	bytecode.store(out, co, st.st_mtime, st.st_size)
