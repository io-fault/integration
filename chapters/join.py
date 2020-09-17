"""
# Join delineated source data into a text file for HTML rendering.
"""
import json
import sys
import typing
import collections

from fault.context import comethod
from fault.context import tools
from fault.context import string

from fault.system import process
from fault.system import files

from fault.project import root

from fault.text import render
from fault.text import nodes
from fault.text import document
from fault.text.types import Paragraph, Fragment
from fault.syntax.types import Area, Address

from .tools import get_properties

def itruncate(lines:[str], indentation='\t', ilevel=string.ilevel):
	"""
	# Truncate the minimum common indentation in &lines.
	"""
	clines = []
	excess = 0xFFFFFFFF
	for l in lines:
		il = ilevel(l)
		clines.append((il, l))
		if il < excess and not l.isspace():
			excess = il
	if excess == 0xFFFFFFFF:
		excess = 0

	return [
		line[max(il - (il - excess), 0):]
		for il, line in clines
	]

def interpret_dictionary_items(items):
	return {
		i[2]['identifier']: (nodes.document.export(i[1][0][1]), i[1][1][1])
		for i in items
	}

def get_parameters(rq, section_id='Parameters'):
	"""
	# Extract parameters from a documentation string.
	"""
	params = rq.select('/section[%s]/dictionary/item' %(section_id,))
	return interpret_dictionary_items(params)

def prefix(path, node):
	"""
	# Adjust the sections in &node to be relative to &path.
	"""
	depth = len(path) - 1
	stack = [x for x in node[1] if x[0] == 'section']

	while stack:
		subsections = []
		for section in stack:
			# Prefix with empty path.
			sd = section[2]
			a = sd['absolute']
			a = path + tuple(a or ())
			sd['absolute'] = a

			# Adjust depth to always be relative.
			sd['selector-multiple'] = None
			sd['selector-level'] = len(sd['absolute']) - 1
			sd['selector-path'] = sd['absolute'][-1:]

			subsections.extend([x for x in section[1] if x[0] == 'section'])
		depth += 1
		stack = subsections

def extract(sub, section):
	"""
	# Extract the mapping from the identified &section removing its node from the tree.
	"""
	r = sub.root[0]
	items = sub.select('/section[%s]/dictionary/item' %(section,))

	# Remove extracted section entirely.
	for i, x in enumerate(r[1]):
		if x[0] == 'section' and x[2]['identifier'] == section:
			del r[1][i]

	return interpret_dictionary_items(items)

def control(**kw):
	"""
	# Construct a CONTROL admonition node.
	"""
	return (
		'admonition', [
			('dictionary', [
				_item(k, v)
				for k, v in kw.items()
			], {})
		],
		{'type': 'CONTROL'}
	)

def type_property_fragments(resolve, node, titled=True):
	"""
	# Construct &Fragment instances for populating a property set to describe the type.
	"""
	typsyntax = node[2]['syntax'].replace('\n', '')
	typref = node[2].get('reference')

	tsf = Fragment(('literal/grave-accent/type/syntax', typsyntax))
	yield tsf

	# The type element of the parameter had a 'reference' property.
	# This gives us a possible link target for the type.
	if typref is not None:
		trf = Fragment(('reference/ambiguous', typref))
		trf = resolve(trf, titled=titled)
		reftype, refsubtype, *local = trf.typepath
		yield Fragment(('/'.join([reftype, refsubtype, 'type'] + local), trf[1]))

def describe_type(resolve, node, titled=True):
	"""
	# Produce tuples used to form `'item'` paragraphs describing the type
	# element found within &node.
	"""
	if not node or not node[1]:
		return ()

	try:
		if node[1][0][0] != 'type' or not node[1][0][2].get('syntax'):
			return ()
	except IndexError:
		return ()

	typnode = node[1][0]
	return type_property_fragments(resolve, typnode, titled=titled)

def property_item(pf):
	"""
	# Construct single paragraph item nodes for populating a set or sequence node.
	"""
	return ('item', [('paragraph', Paragraph.of(pf), {})], {})

def documented_field_item(resolve, element, node, identifier, cast, documentation):
	"""
	# Construct the dictionary item node for a documented field.
	"""
	v_content = [] # Content of the new parameter dictionary item.

	# Build item element for rendering.
	i = ('item', [
		('key', ["(%s)`%s`"%(cast, identifier,)], {}),
		('value', v_content, {}),
	], {'identifier': identifier})

	typ_properties = map(property_item, describe_type(resolve, node))

	# Merge properties of the parameter.
	props = get_properties(documentation)
	if not props:
		v_content.append(('set', list(typ_properties), {}))
	else:
		# Prefix onto existing set.
		documentation[0][1][:0] = typ_properties

	# Copy the documentation from the Parameters section's dictionary item.
	v_content.extend(documentation)

	return i

def undocumented_field_item(resolve, element, node, identifier, cast, documentation=None):
	"""
	# Construct the dictionary item node for representing an undocumented field.
	# The &documentation parameter is provided for type consistency with &documented_field_item.
	"""
	v_content = [] # Content of the new parameter dictionary item.

	# Build item element for rendering.
	i = ('item', [
		('key', ["(%s)`%s`"%(cast, identifier,)], {}),
		('value', v_content, {}),
	], {'identifier': identifier})

	propset = list(map(property_item, describe_type(resolve, node)))
	v_content.append(('set', propset, {},))
	v_content.append((
		'paragraph',
		Paragraph.of(
			Fragment(('literal/grave-accent/ctl/absent', "Undocumented")),
			Fragment(('text/normal', "."))
		),
		{}
	))

	return i

class Text(comethod.object):
	"""
	# Materialization routines for source elements.
	"""

	def getdoc(self, path):
		try:
			p = self.docs[path]
		except KeyError:
			return None
		else:
			if not isinstance(p, nodes.Cursor):
				p = self.docs[path] = nodes.Cursor.from_chapter_text('\n'.join(p))

		return p

	def setdocs(self, path, cursor, section='Elements', _prefix=[('section', [], {})]):
		tmap = extract(cursor, 'Elements')
		self.docs.update((path + (k,), nodes.Cursor.from_chapter_content(_prefix+v[1])) for k, v in tmap.items())

	def r_control(self, node, documented=True, element=(), **ctlkeys):
		ctl = [
			"! CONTROL:\n",
			"\t/type/\n",
			"\t\t" + node[0] + "\n",
		]
		for k, v in ctlkeys.items():
			if v is not None:
				ctl.extend([
					"\t/" + k + "/\n",
					"\t\t" + v + "\n",
				])

		flags = set()
		if not documented:
			flags.add('undocumented')

		if flags:
			ctl.append("\t/flags/\n")
			for f in flags:
				ctl.append("\t\t- `" + f + "`\n")

		# Element properties.
		ctl.append("\t/element/\n")
		try:
			area = node[2]['area']
		except LookupError:
			ctl.append("\t\t- (source/area)``\n")
		else:
			ctl.append("\t\t- (source/area)`{0[0]} {0[1]} {1[0]} {1[1]}`\n".format(*area))

		if element:
			ctl.extend(render.elements([('set', element, {})], adjustment=2))

		return ctl

	def r_root(self, elements):
		yield from self.r_control(elements, syntax=elements[2].get('syntax', None))

		doc = self.getdoc(())
		if doc is not None:
			r = doc.root[0]
			self.setdocs((), doc)

			params = extract(doc, 'Parameters')
			if params:
				sect = r[1][0]
				pd = ('dictionary', [], {})
				sect[1].append(pd)
				for nid, p_documented, i in self.r_parameters(elements, (), r, params):
					pd[1].append(i)

			# Rewrite ambiguous references found in the documentation.
			if r[1]:
				r = self.resolution.rewrite((), r)
				yield from render.chapter(r)

		yield from self.switch((), elements[1])

	def r_inherits(self, path, node):
		lines = []

		resolve = self.resolution.partial(path)
		while node[1]:
			lines = ["! INHERIT:\n"]
			typnode = node[1][0]

			try:
				area = typnode[2]['area']
			except LookupError:
				lines.append("\t- (source/area)``\n")
			else:
				lines.append("\t- (source/area)`{0[0]} {0[1]} {1[0]} {1[1]}`\n".format(*area))

			typdata = list(map(property_item, describe_type(resolve, node)))
			lines.extend(render.elements([('set', typdata, {})], adjustment=1))

			# &describe_type presumes a single type entry for a node.
			del node[1][:1]

		return lines

	@comethod('class')
	@comethod('structure')
	@comethod('exception')
	def r_container(self, path, node):
		yield self.newline
		yield self.section(0, None, path)

		typdata = None
		inherits = ()
		offset = 0
		subnodes = node[1]
		resolve = self.resolution.partial(path)

		# If the container has a type element, it's a metaclass or similar concept.
		try:
			if subnodes[offset][0] == 'type':
				typdata = list(map(property_item, describe_type(resolve, node)))
				offset += 1
		except LookupError:
			pass

		doc = self.docs.get(path, None)
		yield from self.r_control(node, documented=bool(doc), element=typdata)

		# Collect inheritance if any is specified and increment offset for &switch.
		try:
			inherits = subnodes[offset]
		except LookupError:
			inherits = ()
		else:
			if inherits[0] == 'inheritance':
				yield from self.r_inherits(path, subnodes[offset])
				offset += 1

		if doc:
			sub = nodes.Cursor.from_chapter_text('\n'.join(doc))
			self.setdocs(path, sub, section='Elements')

			params = extract(sub, 'Parameters')
			if params:
				sect = r[1][0]
				pd = ('dictionary', [], {})
				sect[1].append(pd)
				for nid, p_documented, i in self.r_parameters(node, path, sub.root, params):
					pd[1].append(i)

			# Rewrite ambiguous references found in the documentation.
			r = self.resolution.rewrite(path, sub.root[0])

			for x in r[1]:
				yield from render.tree(x)

		yield from self.switch(path, subnodes[offset:])

	def r_parameters(self, node, path, nodes, params):
		resolve = self.resolution.partial(path)
		for nid, n in nodes:
			if nid in params:
				k, v = params[nid]
				yield nid, True, documented_field_item(resolve, node, n, nid, 'parameter', v)
			else:
				yield nid, False, undocumented_field_item(resolve, node, n, nid, 'parameter')

	def section(self, rdepth, rmult, path):
		p = render.section_path(rdepth, rmult, *path)
		p.append("\n")
		return "".join(p)

	@comethod('include')
	def r_void(self, path, node):
		"""
		# Unsupported node type.
		"""
		return ()

	@comethod('chapter')
	def r_text(self, path, node):
		"""
		# Rewrite references in the text tree and render the changes.
		"""
		r = self.resolution.rewrite(path, node)
		yield from render.chapter(r)

	@comethod('define')
	@comethod('data')
	def r_source(self, path, node):
		"""
		# Render a capture of the source after the documentation.
		"""
		doc = self.getdoc(path)

		# Retrieve the type element.
		resolve = self.resolution.partial(path)
		typdata = list(map(property_item, describe_type(resolve, node)))

		yield self.newline
		yield self.section(0, None, path)
		yield from self.r_control(node, documented=bool(doc), element=typdata)
		if doc is not None:
			if doc.root[0][1]:
				yield from render.chapter(doc.root[0])

		yield "#!source\n"
		for x in itruncate(self.selectlines(node)):
			yield "\t" + x

	def r_element(self, path, node):
		"""
		# Emit a section containing the element's documentation.

		# If the documentation of the element contains a `Parameters`
		# section, integrate it into the element's section along with
		# any undocumented parameters.
		"""
		yield self.newline
		yield self.section(0, None, path)

		doc = self.docs.get(path, None)

		# Retrieve the type of the element.
		resolve = self.resolution.partial(path)
		typdata = list(map(property_item, describe_type(resolve, node)))
		yield from self.r_control(node, documented=bool(doc), element=typdata)

		param_nodes = []
		try:
			for n in node[1]:
				if n and n[0] in {'parameter', 'option', 'mapping', 'vector'}:
					param_nodes.append((n[2]['identifier'], n))
		except:
			# Not a parameterized element.
			pass

		# Parse documentation and identify documented parameters.
		documented = set()
		if doc:
			sub = nodes.Cursor.from_chapter_text('\n'.join(doc))
			params = extract(sub, 'Parameters')
			r = sub.root[0]
			prefix(path, r)
			sect = r[1][0]

			# Add new parameters.
			pd = ('dictionary', [], {})
			sect[1].append(pd)

			# Process the parameters section.
			for nid, p_documented, i in self.r_parameters(node, path, param_nodes, params):
				pd[1].append(i)
				if p_documented:
					documented.add(nid)
		else:
			params = {}
			r = ('chapter', [], {})

		# Callable signature production.
		if node[0] not in {'property', 'data', 'field', 'import'}:
			# Only show required parameters and documented options.
			dparams = (
				# If the element provides an override syntax,
				# prefer it over the exact identifier.
				x[1][2].get('syntax', x[0]) for x in param_nodes
				if x[0] in documented or x[1][0] != 'option'
			)
			sig = '(signature)' + "`%s(%s)`" % (path[-1], ", ".join(dparams))
			sig += self.newline
			yield sig
			# Break for paragraph.
			yield self.newline

		# Rewrite ambiguous references found in the documentation.
		if r[1]:
			r = self.resolution.rewrite(path, r)
			yield from render.chapter(r)

	def switch(self, path, nodes, *suffix):
		for x in nodes:
			p = path + (x[2].get('identifier'),)
			try:
				selected_method = self.comethod(x[0], *suffix)
			except comethod.MethodNotFound:
				yield from self.r_element(p, x)
			else:
				yield from selected_method(p, x)

	@tools.cachedproperty
	def source(self):
		with self.source_path.fs_open('r') as f:
			return list(f)

	def selectlines(self, node):
		start, stop = node[2]['area']
		a = Area((Address(start), Address(stop)))

		prefix, suffix, lines = a.select(self.source)
		lines[0] = prefix + lines[0]
		lines[-1] = lines[-1] + suffix
		return lines

	def __init__(self, resolution, elements, docs, data, source):
		self.resolution = resolution
		self.elements = elements
		self.source_path = source
		self.newline = "\n"
		self.docs = docs
		self.data = data

def split_element(project, factor):
	"""
	# Given a project relative factor path, split the path isolating
	# the factor's element from the path and construct a triple containing
	# the link, title, and target type describing the factor path.
	"""
	parts = project.split(factor)
	pfactor = str(project.factor)

	if parts is not None and parts[1]:
		link = "{0}#{1}".format(str(parts[0]), parts[1])
		title = "[{0}.{1}.{2}]".format(pfactor, str(parts[0]), parts[1])
		target_type = 'factor-element'
	else:
		link = "{0}".format(str(factor))
		title = "[{0}.{1}]".format(pfactor, str(factor))
		target_type = 'project-factor'

	return link, title, target_type

def relation(origin, target):
	"""
	# Identify the relation of the &target project to &origin project.
	"""
	if target.factor == origin.factor:
		return 'project-local'
	elif target.factor.container == origin.factor.container:
		return 'context-local'
	else:
		return 'remote'

def dr_absolute_path(requirements, context, project, reference):
	"""
	# Resolve an absolute reference.
	"""
	fpath = root.types.factor@reference
	try:
		target = context.split(fpath)
	except LookupError:
		try:
			target = requirements.split(fpath)
		except LookupError:
			return '[' + str(reference) + ']', 'http://fault.io/dev/null', 'invalid', 'none'

	product, target_project, factor = target

	if factor:
		link, title, target_type = split_element(target_project, factor)
	else:
		target_type = 'project-name'
		link = str(path)
		title = ''

	rel = relation(project, target_project)
	if rel == 'remote':
		link = target_project.identifier + '/' + link
	elif rel == 'context-local':
		link = str(target_project.factor) + '/' + link
	else:
		# No link adjustment necessary for project-local.
		pass

	return title, link, target_type, rel

def dr_context_path(context, project, reference):
	"""
	# Resolve a root-Context relative reference.
	"""
	local = 'context-local'
	target_type = None
	cpath = root.types.factor
	for cpath in project.itercontexts():
		pass
	cpath = cpath.container

	path = cpath@reference
	try:
		product, target_project, factor = context.split(path)
	except LookupError:
		return '[' + str(path) + ']', 'http://fault.io/dev/null', 'invalid', 'none'

	if factor:
		link, title, target_type = split_element(target_project, factor)
		link = str(target_project.factor) + '/' + link
	else:
		target_type = 'project-name'
		link = str(path)
		title = ''

	if target_project.identifier == project.identifier:
		# self reference
		local = 'project-local'

	return title, link, target_type, local

def dr_project_path(project, reference):
	"""
	# Resolve a Project relative reference.
	"""
	path = root.types.factor@reference
	parts = project.split(path)
	title = ''

	if parts is not None:
		factor, element = parts
		if element:
			link = "{0}#{1}".format(str(factor), element)
			title = "[{0}.{1}]".format(str(factor), element)
		else:
			link = str(factor)
	else:
		link = str(path)

	return title, link

def index(root, deque=collections.deque, none={}):
	"""
	# Construct an index of elements using the identifier paths.
	"""
	subnodes = set(x[2].get('identifier') for x in root[1])
	idx = {(): (root, subnodes)}

	q = deque()
	q.extend(((), x) for x in root[1])
	while q:
		p, n = q.popleft()
		try:
			ni = n[2].get('identifier')
		except KeyError:
			print(n)
			continue
		except IndexError:
			continue

		# Descend
		if ni:
			sp = p + (ni,)
			try:
				subnodes = set(x[2].get('identifier') for x in n[1])
			except IndexError:
				subnodes = set()
			subnodes.discard(None)
			idx[sp] = (n, subnodes)
			q.extend((sp, x) for x in n[1])

	return idx

def match(index, path, subpath):
	"""
	# Check for the presence of &subpath in &path in &index and return
	# the level of consistency it has at that location.

	# [ Returns ]
	# Returns the number of leading &subpath items that matched at that position.
	"""
	sub = (None, ())
	consistency = 0

	for x in subpath:
		sub = index.get(path, (None, ()))
		if x not in sub[1]:
			break
		consistency += 1
		path += (x,)

	return consistency

def find(index, path:typing.Sequence[str], rpath:typing.Sequence[str]):
	"""
	# Find all the matches for &rpath in &index by ascending through &path.

	# [ Returns ]
	# A sorted list identifying all non-zero matches is returned where the
	# first entry is the deepest match in the nearest path. Consistency
	# is given preference over location.
	"""
	n = len(rpath)
	matches = []

	while path:
		parts = match(index, path, rpath)
		if parts > 0:
			matches.append((parts, path))
		path = path[:-1]

	parts = match(index, (), rpath)
	if parts > 0:
		matches.append((parts, path))

	matches.sort(key=(lambda x: (x[0], len(x[1]))), reverse=True)
	return matches

class Resolution(comethod.object):
	"""
	# Reference resolution interface for factored projects.
	"""

	def __init__(self, requirements, context, project, factor):
		self.index = None
		self.requirements = requirements
		self.context = context
		self.project = project
		self.factor = factor

	@comethod('key')
	@comethod('paragraph')
	def disambiguate(self, element, path, node, *suffix, AR=['reference', 'ambiguous']):
		assert node[0] in {'paragraph', 'key'}

		if isinstance(node[1], Paragraph):
			p = node[1]
		else:
			p = nodes.document.export(node[1])

		return p.__class__(
			(self.resolve(element, x) if x.typepath[:2] == AR else x)
			for x in p
		)

	# Anything that is guaranteed to not contain references.
	@comethod('syntax')
	@comethod('line')
	def transparent(self, element, path, node, *suffix):
		return node[1]

	def switch(self, element, path, node, *suffix):
		subnodes = node[1]

		for i, x in zip(range(len(subnodes)), subnodes):
			xid = x[2].get('identifier') or None
			if xid is not None:
				p = path + (xid,)
			else:
				p = path

			try:
				method = self.comethod(x[0], *suffix)
				subnodes[i] = (x[0], method(element, p, x)) + tuple(x[2:])
			except comethod.MethodNotFound:
				# Not being re-written.
				self.switch(element, p, x, *suffix)

	def rewrite(self, element, root):
		"""
		# Rewrite the references in the node tree &root as relative IRI's.
		# [ Parameters ]
		# /element/
			# The identifier path of the documented element.
		# /root/
			# The documentation's element tree.
		"""
		self.switch(element, (), root)
		return root

	def resolve(self, path, fragment, depth=0, titled=True):
		local = ''
		title = ''
		name_type = ''
		reference = fragment.data
		reftype = fragment.typepath[2:]
		if reftype:
			reftype = reftype[0]

		# Count leading dots selecting the search context.
		leading = 0
		for x in reference:
			if x != '.':
				break
			leading += 1

		if leading > 2:
			# Unknown Scope
			return fragment
		elif leading == 2:
			# Corpus Relative; root context.
			depth += 1
			title, link, name_type, local = dr_context_path(self.context, self.project, reference.lstrip('.'))
		elif leading == 1:
			# Project Relative.
			title, link = dr_project_path(self.project, reference.lstrip('.'))
			local = 'project-local'
		else:
			if reference[:1] == '@':
				title, link, name_type, local = dr_absolute_path(self.requirements, self.context, self.project, reference[1:])
			else:
				# Element Context Relative.
				local = 'factor-local'
				rpath = reference.split('.')
				targets = find(self.index, path, rpath)
				if targets:
					mdepth, prefix = targets[0]
					target = prefix + tuple(rpath[:mdepth])

					target_node = self.index[target][0]
					target_is_factor = target_node[2].get('factor') or None
					if target_is_factor:
						# The targeted element is potentially from a factor.
						target_path = target_node[2].get('path', [])
						target_relative = target_node[2].get('relative', 0)
						target_element = rpath[mdepth:]

						if target_relative:
							factor = ((self.project.factor // self.factor) ** target_relative) + target_path
						else:
							factor = self.factor.__class__.from_sequence(target_path)

						target_factor = list(factor.iterpoints())
						redirect = '.'.join(target_factor + target_element)
						absdata = dr_absolute_path(self.requirements, self.context, self.project, redirect)
						title, link, name_type, local = absdata
					else:
						name_type = target_node[0]
						link = '#' + '.'.join(target)
						title = '[' + reference + ']'
				else:
					# No such element.
					local = 'invalid'
					link = "#XXX-{0}".format(reference.lstrip('.'))

		if not titled:
			title = ''

		reftype = ['reference', 'hyperlink', local, name_type or reftype or 'unknown']
		return fragment.__class__(('/'.join(reftype), link + title))

	def partial(self, path, **kw):
		return tools.partial(self.resolve, path, **kw)

	def add_index(self, elements):
		self.index = index(elements)

def load(f):
	try:
		return json.load(f)
	except json.decoder.JSONDecodeError:
		f.seek(0)
		data = f.read()
		data = data.replace(',]', ']')
		data = data.replace(',}', '}')
		return json.loads(data)

def transform(resolution, datadir:files.Path, source:files.Path):
	re = (datadir/"elements.json")
	dd = (datadir/"documented.json")
	rd = (datadir/"documentation.json")
	rt = (datadir/"data.json")
	tf = (datadir/"fates.json")
	test_factor = (tf.fs_type() == 'file')

	with re.fs_open('r') as f:
		elements = load(f)
		resolution.add_index(elements)

	try:
		with dd.fs_open('r') as f:
			keys = load(f)
		with rd.fs_open('r') as f:
			strings = load(f)
	except:
		keys = ()
		strings = ()
	docs = dict(zip(map(tuple,keys),strings))

	try:
		with rt.fs_open('r') as f:
			keys, datas = load(f)
			data = dict(zip(map(tuple,keys),datas))
	except:
		data = dict()

	t = Text(resolution, elements, docs, data, source)
	return t.r_root(elements)
