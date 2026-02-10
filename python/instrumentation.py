"""
# AST manipulations for injecting coverage counters and profile timers into Python modules.
"""
import ast
import builtins
import functools

from . import module
from . import source

try:
	FunctionTypes = (ast.FunctionDef, ast.AsyncFunctionDef)
except AttributeError:
	FunctionTypes = (ast.FunctionDef,)

ContainerTypes = (ast.Module, ast.ClassDef)

# Profile suspend/resume nodes.
SuspendClasses = (ast.Yield, ast.YieldFrom, ast.Await)

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

module_context = """
if True:
	import collections as _fi_cl
	import atexit as _fi_ae
	import functools as _fi_ft
	import os as _fi_os
	import builtins as _fi_bn

	def _fi_mkdir(path, Retry=32, range=_fi_bn.range, makedirs=_fi_os.makedirs):
		for x in range(Retry):
			try:
				makedirs(path)
			except FileExistsError:
				# Tests should be able to run in parallel, so expect runtime conflicts.
				pass
			else:
				break
		return path

	def _fi_identify_path(mtype):
		# .metrics/../{mtype}/{pid}/{module}/{project}/{factor}/{test}
		import sys, os, collections

		if 'PROCESS_IDENTITY' in os.environ:
			pid = os.environ['PROCESS_IDENTITY']
		else:
			pid = str(os.getpid())

		if 'METRICS_CAPTURE' in os.environ:
			# If capture is defined, qualify with the module name.
			path = os.environ['METRICS_CAPTURE']
			path += '/' + mtype
			path += '/' + pid
			path += '/' + __name__
		else:
			try:
				if __metrics_trap__ is None:
					# No destination.
					return
			except NameError:
				return

			# Resolve __metrics_trap__ global at exit in order to allow the runtime
			# to designate it given compile time absence.
			path = __metrics_trap__
			path += '/' + mtype
			path += '/' + pid

		path += '/' + os.environ.get('METRICS_IDENTITY', '.fault-python')
		return path

	def _fi_alloc_dir(mtype, subdir, *, mk=_fi_mkdir, cp=_fi_identify_path):
		return mk(cp(mtype) + '/' + subdir)
	del _fi_mkdir, _fi_identify_path

	if 'coverage' in __metrics__:
		_fi_counters__ = _fi_cl.Counter()
		def _fi_record_coverage(counters=_fi_counters__, adir=_fi_alloc_dir):
			import os
			if 'METRICS_ISOLATION' in os.environ:
				mid = os.environ['METRICS_ISOLATION']
			else:
				mid = 'unspecified'

			path = adir('coverage', '.fault-syntax-counters')
			import sys, os, collections

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
				f.writelines(['%s %d %s\\n' %(mid, len(events[x]), x) for x in sources])

			with open(path + '/areas', 'a') as f:
				for x in sources:
					f.writelines(['%d %d %d %d\\n' % k for k in events[x]])

			with open(path + '/counts', 'a') as f:
				for x in sources:
					f.writelines(['%d\\n' %(c,) for c in occurrences[x]])

		_fi_ae.register(_fi_record_coverage)

		try:
			_FI_INCREMENT__ = _fi_ft.partial(_fi_cl._count_elements, _fi_counters__)
		except:
			_FI_INCREMENT__ = _fi_counters__.update

		def _FI_COUNT__(area, rob, F=__file__, C=_FI_INCREMENT__):
			C(((F, area),))
			return rob
		del _fi_record_coverage

	if 'profile' in __metrics__:
		_fi_timings__ = _fi_cl.defaultdict(list)
		def _fi_record_profile(timings=_fi_timings__, adir=_fi_alloc_dir):
			def name(module, object_path):
				if module == __name__:
					return object_path or '-'
				else:
					return '/'.join((module or '-', object_path or '-'))
			path = adir('profile', '.fault-timing-deltas')
			with open(path + '/timings', 'a') as f:
				for src, times in timings.items():
					cfactor, celement, element = src
					f.write("%s: %s\\n" %(element, name(cfactor, celement)))
					f.writelines("\t%d-%d\\n" %(time, delta) for time, delta in times)

		try:
			from fault.system.clocks import Monotonic as _fi_mclock
		except ImportError:
			from time import perf_counter_ns as _FI_CLOCK_SNAPSHOT__
		else:
			_FI_CLOCK_SNAPSHOT__ = _fi_mclock().get
			del _fi_mclock
		_fi_ae.register(_fi_record_profile)

		from threading import local as _fi_thread_local
		_FI_PROFILE_LOCALS____ = _fi_thread_local()
		del _fi_thread_local
		_FI_PROFILE_COUNTER____ = _fi_cl.Counter

		def _FI_NOTE_TIMING__(CID, ELEMENT, TIME, CD, LD, TS=_FI_CLOCK_SNAPSHOT__, sum=sum, TR=_fi_timings__):
			d = TS() - TIME
			CD[ELEMENT] += d
			TR[(CID[0], CID[1], ELEMENT)].append((d, sum(LD.values())))

	# Limit names left in the module globals.
	del _fi_bn, _fi_os, _fi_ft, _fi_cl, _fi_ae, _fi_alloc_dir
""".strip() + '\n'

count_boolop_expression = "(_FI_INCREMENT__(((__file__, %r),)) or INSTRUMENTATION_ERROR)"
count_call_expression = "_FI_COUNT__(%r,None)"

# When instrumenting a generator or coroutine, these signal functions are built to
# record the time spent outside. Timings are recorded using the resident deltas None key.
profile_suspension_signals = """
if True:
	def _fi_suspend____(V):
		nonlocal _fi_suspend_time____
		nonlocal _fi_caller_residency____
		nonlocal _fi_caller_identity____
		nonlocal _fi_resident_deltas____
		# Forward timings to caller for tracking residency and hold timestamp for resume.
		_fi_suspend_time____ = _FI_CLOCK_SNAPSHOT__()

		_FI_PROFILE_LOCALS____.fi_profile_residency = _fi_caller_residency____
		_FI_PROFILE_LOCALS____.fi_caller_identity = _fi_caller_identity____
		return V

	def _fi_resume____(V):
		nonlocal _fi_suspend_time____
		nonlocal _fi_caller_residency____
		nonlocal _fi_caller_identity____
		nonlocal _fi_resident_deltas____

		if 'fi_profile_residency' in _FI_PROFILE_LOCALS____.__dict__:
			_fi_caller_residency____ = _FI_PROFILE_LOCALS____.fi_profile_residency
		else:
			_fi_caller_residency____ = _FI_PROFILE_COUNTER____()
		_FI_PROFILE_LOCALS____.fi_profile_residency = _fi_resident_deltas____

		# Push caller identity.
		_fi_caller_identity____ = getattr(_FI_PROFILE_LOCALS____, 'fi_caller_identity', (None, None))
		_FI_PROFILE_LOCALS____.fi_caller_identity = (__name__, _fi_identity____)

		# Update start to exclude the suspended time.
		_fi_resident_deltas____[None] += _FI_CLOCK_SNAPSHOT__() - _fi_suspend_time____
		_fi_suspend_time____ = None
		return V
"""

# The root of a profiled block. Class definitions and module bodies are also instrumented.
profile_transaction = """
if True:
	try:
		_fi_suspend____ = None
		_fi_resume____ = None
		_fi_start_time____ = None
		_fi_suspend_time____ = None
		_fi_caller_residency____ = None
		_fi_resident_deltas____ = _FI_PROFILE_COUNTER____()
		_fi_identity____ = %r

		# Push caller identity.
		_fi_caller_identity____ = getattr(_FI_PROFILE_LOCALS____, 'fi_caller_identity', (None, None))
		_FI_PROFILE_LOCALS____.fi_caller_identity = (__name__, _fi_identity____)

		if 'fi_profile_residency' in _FI_PROFILE_LOCALS____.__dict__:
			_fi_caller_residency____ = _FI_PROFILE_LOCALS____.fi_profile_residency
		else:
			_fi_caller_residency____ = _FI_PROFILE_COUNTER____()
		_FI_PROFILE_LOCALS____.fi_profile_residency = _fi_resident_deltas____
		_fi_start_time____ = _FI_CLOCK_SNAPSHOT__()

		# Insertion point.
		pass
	finally:
		# Restore
		_FI_PROFILE_LOCALS____.fi_profile_residency = _fi_caller_residency____
		_FI_PROFILE_LOCALS____.fi_caller_identity = _fi_caller_identity____

		_FI_NOTE_TIMING__(_fi_caller_identity____, _fi_identity____, _fi_start_time____, _fi_caller_residency____, _fi_resident_deltas____)

		# Class and modules bodies are instrumented, so always clean up the names.
		del _fi_start_time____, _fi_suspend_time____
		del _fi_caller_identity____, _fi_caller_residency____, _fi_resident_deltas____
		del _fi_suspend____, _fi_resume____
"""

# Expression source for calling the suspension signals.
profile_suspend_expression = "_fi_suspend____(None)"
profile_resume_expression = "_fi_resume____(None)"

def construct_call_increment(node, area, path='/dev/null', lineno=1):
	s = count_call_expression % (area,)
	p = ast.parse(s, path)
	k = p.body[0]

	source.node_inherit_address(k, node)
	update = functools.partial(k.value.args.__setitem__, -1)
	return k, update

def construct_boolop_increment(node, area, path='/dev/null', lineno=1):
	s = count_boolop_expression % (area,)
	p = ast.parse(s, path)
	expr = p.body[0]

	source.node_inherit_address(expr, node)
	update = functools.partial(expr.value.values.__setitem__, 1)
	return expr, update

def construct_profile_trap(identifier, container, nodes, path='/dev/null', lineno=1, prefix=[]):
	src = profile_transaction %(identifier,)
	tree = ast.parse(src, path)
	trap = tree.body[0].body[0] # try: block

	trap.body[-1:-1] = prefix + nodes
	assert isinstance(trap.body[-1], ast.Pass)
	del trap.body[-1]

	return trap

def construct_profile_trap_suspend(identifier, container, nodes, path='/dev/null', lineno=1):
	src = profile_suspension_signals
	signals = ast.parse(src, path).body[0].body
	return construct_profile_trap(identifier, container, nodes, prefix=signals, path=path, lineno=lineno)

def construct_initialization_nodes(ln_offset, path="/dev/null"):
	"""
	# Construct instrumentation initialization nodes for injection into an &ast.Module body.
	"""

	nodes = ast.parse(module_context, path)
	source.node_shift_line(nodes, ln_offset)
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

	instrument(record, path, noded, area)

def find_suspend_expressions(node, isinstance=isinstance):
	"""
	# Visit the descending nodes in &node looking for yields and awaits.
	"""

	if hasattr(node, 'value') and isinstance(node.value, SuspendClasses):
		yield node

	# Descend uncondtionally; even when matches are found, they can be nested.
	for sub in ast.iter_child_nodes(node):
		yield from find_suspend_expressions(sub)

def qualify_node_paths(path, fields):
	"""
	# Qualify definitions nodes with their qualified path and
	# yield them for profile instrumentation.
	"""

	for node in fields:
		if isinstance(node, ContainerTypes):
			node._f_path = path + [node.name]
			yield from qualify_node_paths(node._f_path, ast.iter_child_nodes(node))
		elif isinstance(node, FunctionTypes):
			node._f_path = path + [node.name]
			yield node
		else:
			yield from qualify_node_paths(path, ast.iter_child_nodes(node))

def inject_suspend_expressions(node):
	suspend_call = ast.parse(profile_suspend_expression).body[0].value
	resume_call = ast.parse(profile_resume_expression).body[0].value

	yield_expr = node.value
	resume_call.args[0] = yield_expr

	if yield_expr.value is not None:
		suspend_call.args[0] = yield_expr.value or suspend_call.args[0]
	yield_expr.value = suspend_call

	return resume_call

def walk_within(tree, exceptions):
	"""
	# Walk the nodes of &tree without descending into any &exceptions types.

	# Primarily used by profiling to avoid instrumenting nested functions.
	"""

	for n in ast.iter_child_nodes(tree):
		if isinstance(n, exceptions):
			continue
		yield n
		yield from walk_within(n, exceptions)

def inject_profiling_nodes(tree):
	"""
	# Modify the definitions in &tree to record the execution times.
	"""

	# Gather functions and qualify their nodes with their class paths.
	qualified = list(qualify_node_paths([], ast.iter_child_nodes(tree)))

	# Inject instrumentation into functions.
	for node in qualified:
		suspensions = 0
		if isinstance(node, FunctionTypes):
			for sn in walk_within(node, FunctionTypes):
				if isinstance(getattr(sn, 'value', None), SuspendClasses):
					sn.value = inject_suspend_expressions(sn)
					suspensions += 1

		replaced = construct_profile_trap_suspend('.'.join(node._f_path), None, node.body)
		del node.body[:]
		node.body.append(replaced)

def compile(factor, source, path, constants,
		parse=source.parse,
		hash=module.hash_syntax,
		filter=visit,
		record=None,
		instrumentation=set(),
	):
	"""
	# Compile the Python source of a module, &source, into an AST with the requested
	# &instrumentation.
	"""
	srclines, tree, nodes = parse(source, path, filter=visit)

	# Coverage before profiling.
	if 'coverage' in instrumentation:
		for noded in nodes:
			if not hasattr(noded[0], '_f_area'):
				continue
			if isinstance(noded[0], (ast.expr_context, ast.slice)):
				continue

			apply(record, path, noded)

	if 'profile' in instrumentation:
		tree.name = factor
		inject_profiling_nodes(tree)
		init_body = construct_initialization_nodes(len(srclines)).body
		tree.body[0:0] = init_body

		# Handle module body as a one off
		init_node_count = len(init_body)
		module_profile = construct_profile_trap("", None, tree.body[init_node_count:])
		del tree.body[init_node_count:]
		tree.body.append(module_profile)
	else:
		# Insert instrumentation initialization.
		assert 'coverage' in instrumentation
		init_body = construct_initialization_nodes(len(srclines)).body
		tree.body[0:0] = init_body

	# Add hash and canonical factor path.
	constants.extend([
		('__factor__', factor),
		('__source_hash__', hash(source)),
		('__metrics__', instrumentation),
	])
	return module.inject(tree, constants)
