"""
# Join delineated source data into a text file for subsequent rendering.
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
from fault.project import system as lsf
from fault.syntax.types import Area, Address

from fault.text import render
from fault.text.io import structure_chapter_lines
from fault.text.io import structure_paragraph_element as ipara
from fault.text.types import Paragraph, Fragment

from .protocol import setdirectory
from . import query

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

def interpret_directory_items(items):
	return {
		i[2]['identifier']: (ipara(i[1][0]), i[1][1][1])
		for i in items
	}

def prefix(path, element):
	"""
	# Adjust the sections in &element to be relative to &path.
	"""
	depth = len(path) - 1
	stack = [x for x in element[1] if x[0] == 'section']

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
	# Extract the mapping from the identified &section removing its element from the tree.
	"""
	r = sub.root[0]
	items = sub.select('/section[%s]/directory/item' %(section,))

	# Remove extracted section entirely.
	for i, x in enumerate(r[1]):
		if x[0] == 'section' and x[2]['identifier'] == section:
			del r[1][i]

	return interpret_directory_items(items)

def section_items(chapter, section):
	"""
	# Get the first directory in &section and its interpreted items.
	"""
	d = chapter.fork('/section[%s]/directory#1' %(section,))
	if d.root:
		pd = d.root[0]
	else:
		pd = ('directory', [], {})
	return pd, interpret_directory_items(d.select('item'))

def insert_before(type, elements, element):
	for i, n in enumerate(elements):
		if n[0] == type:
			elements.insert(i, element)
			return

	elements.append(element)

def control(**kw):
	"""
	# Construct a CONTROL admonition element.
	"""
	return (
		'admonition', [
			('directory', [
				_item(k, v)
				for k, v in kw.items()
			], {})
		],
		{'type': 'CONTROL'}
	)

def type_property_fragments(resolve, element, titled=True):
	"""
	# Construct &Fragment instances for populating a property set to describe the type.
	"""
	typsyntax = element[2]['syntax'].replace('\n', '')
	typref = element[2].get('reference')

	tsf = Fragment(('literal/grave-accent/type/syntax', typsyntax))
	yield tsf

	# The type element of the parameter had a 'reference' property.
	# This gives us a possible link target for the type.
	if typref is not None:
		trf = Fragment(('reference/ambiguous', typref))
		trf = resolve(trf, titled=titled)
		reftype, refsubtype, *local = trf.typepath
		yield Fragment(('/'.join([reftype, refsubtype, 'type'] + local), trf[1]))

def describe_type(resolve, element, titled=True):
	"""
	# Produce tuples used to form `'item'` paragraphs describing the type
	# element found within &element.
	"""
	if not element or not element[1]:
		return ()

	try:
		if element[1][0][0] != 'type' or not element[1][0][2].get('syntax'):
			return ()
	except IndexError:
		return ()

	typ = element[1][0]
	return type_property_fragments(resolve, typ, titled=titled)

def property_item(pf):
	"""
	# Construct single paragraph item elements for populating a set or sequence element.
	"""
	return ('item', [('paragraph', Paragraph.of(pf), {})], {})

def documented_field_item(cast, resolve, context, element, identifier, documentation):
	"""
	# Construct the directory item element for a documented field.
	"""
	v_content = [] # Content of the new parameter directory item.

	# Build item element for rendering.
	i = ('item', [
		('key', ["(%s)`%s`"%(cast, identifier,)], {}),
		('value', v_content, {}),
	], {'identifier': identifier})

	typp = map(property_item, describe_type(resolve, element))

	# Merge properties of the parameter.
	props = dict(setdirectory.select(documentation))
	if not props:
		v_content.append(('set', list(typp), {}))
	else:
		# Prefix onto existing set.
		documentation[0][1][:0] = typp

	# Copy the documentation from the Parameters section's directory item.
	v_content.extend(documentation)

	return i

def undocumented_field_item(cast, resolve, context, element, identifier, documentation=None):
	"""
	# Construct the directory item element for representing an undocumented field.
	# The &documentation parameter is provided for type consistency with &documented_field_item.
	"""
	v_content = [] # Content of the new parameter directory item.

	# Build item element for rendering.
	i = ('item', [
		('key', ["(%s)`%s`"%(cast, identifier,)], {}),
		('value', v_content, {}),
	], {'identifier': identifier})

	typp = list(map(property_item, describe_type(resolve, element)))
	v_content.append(('set', typp, {},))
	v_content.append((
		'paragraph',
		Paragraph.of(
			Fragment(('literal/grave-accent/control/absent', "Undocumented")),
			Fragment(('text/normal', "."))
		),
		{}
	))

	return i

class Text(comethod.object):
	"""
	# Linked chapter construction for factor elements.
	"""

	def getdoc(self, path):
		try:
			p = self.docs[path]
		except KeyError:
			return None
		else:
			if not isinstance(p, query.Cursor):
				p = self.docs[path] = query.navigate(structure_chapter_lines(p))

		return p

	def setdocs(self, path, cursor, section='Elements'):
		tmap = extract(cursor, 'Elements')
		self.docs.update(
			(path + (k,), query.navigate(('chapter', v[1], {})))
			for k, v in tmap.items()
		)

	def r_control(self, factorelement, documented=True, element=(), **ctlkeys):
		ctl = [
			"! CONTROL:\n",
			"\t/type/\n",
			"\t\t" + factorelement[0] + "\n",
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
		ctl.append("\t\t- (control)`property-set`\n")
		try:
			area = factorelement[2]['area']
		except LookupError:
			ctl.append("\t\t- (source/area)``\n")
		else:
			ctl.append("\t\t- (source/area)`{0[0]} {0[1]} {1[0]} {1[1]}`\n".format(*area))

		if element:
			ctl.extend(render.elements([('set', element, {})], adjustment=2))

		return ctl

	def r_root(self, factor):
		yield from self.r_control(factor, syntax=factor[2].get('syntax', None))

		doc = self.getdoc(())
		if doc is not None:
			self.setdocs((), doc, section='Elements')
			r = doc.root[0]

			pd, params = section_items(doc, 'Parameters')
			if params:
				pi = pd[1]
				del pi[:]
				for nid, p_documented, i in self.r_parameters(factor, (), r, params):
					pi.append(i)

			# Rewrite ambiguous references found in the documentation.
			if r[1]:
				r = self.resolution.rewrite((), r)
				yield from render.chapter(r)

		yield from self.switch((), factor[1])

	def r_inherits(self, path, element):
		lines = []

		resolve = self.resolution.partial(path)
		while element[1]:
			lines = ["! INHERIT:\n"]
			lines.append("\t- (control)`property-set`\n")
			typ = element[1][0]

			try:
				area = typ[2]['area']
			except LookupError:
				lines.append("\t- (source/area)``\n")
			else:
				lines.append("\t- (source/area)`{0[0]} {0[1]} {1[0]} {1[1]}`\n".format(*area))

			typdata = list(map(property_item, describe_type(resolve, element)))
			lines.extend(render.elements([('set', typdata, {})], adjustment=1))

			# &describe_type presumes a single type entry for an element.
			del element[1][:1]

		return lines

	@comethod('class')
	@comethod('structure')
	@comethod('exception')
	def r_container(self, path, element):
		yield self.newline
		yield self.section(0, None, path)

		typdata = None
		inherits = ()
		offset = 0
		subelements = element[1]
		resolve = self.resolution.partial(path)

		# If the container has a type element, it's a metaclass or similar concept.
		try:
			if subelements[offset][0] == 'type':
				typdata = list(map(property_item, describe_type(resolve, element)))
				offset += 1
		except LookupError:
			pass

		doc = self.getdoc(path)
		yield from self.r_control(element, documented=bool(doc), element=typdata)

		# Collect inheritance if any is specified and increment offset for &switch.
		try:
			inherits = subelements[offset]
		except LookupError:
			inherits = ()
		else:
			if inherits[0] == 'inheritance':
				yield from self.r_inherits(path, subelements[offset])
				offset += 1

		if doc:
			self.setdocs(path, doc, section='Elements')
			pd, params = section_items(doc, 'Parameters')
			if params:
				pi = pd[1]
				del pi[:]
				for nid, p_documented, i in self.r_parameters(elements, (), r, params):
					pi.append(i)

			# Rewrite ambiguous references found in the documentation.
			r = self.resolution.rewrite(path, doc.root[0])
			prefix(path, r)
			yield from render.chapter(r)

		yield from self.switch(path, subelements[offset:])

	def r_parameters(self, element, path, parameters, documented):
		resolve = self.resolution.partial(path)

		# Generate elements for each parameter,
		# and join with the documentation associated with the &element.
		for pid, pelement in parameters:
			if pid in documented:
				yield pid, True, documented_field_item('parameter',
					resolve, element,
					pelement, pid,
					documented[pid][1]
				)
			else:
				yield pid, False, undocumented_field_item('parameter',
					resolve, element,
					pelement, pid
				)

	def section(self, rdepth, rmult, path):
		p = render.section_path(rdepth, rmult, *path)
		p.append("\n")
		return "".join(p)

	@comethod('include')
	def r_void(self, path, element):
		"""
		# Unsupported element type.
		"""
		return ()

	@comethod('chapter')
	def r_text(self, path, element):
		"""
		# Rewrite references in the text tree and render the changes.
		"""
		r = self.resolution.rewrite(path, element)
		yield from render.chapter(r)

	@comethod('define')
	@comethod('data')
	def r_source(self, path, element):
		"""
		# Render a capture of the source after the documentation.
		"""
		doc = self.getdoc(path)

		# Retrieve the type element.
		resolve = self.resolution.partial(path)
		typdata = list(map(property_item, describe_type(resolve, element)))

		yield self.newline
		yield self.section(0, None, path)
		yield from self.r_control(element, documented=bool(doc), element=typdata)

		if doc is not None:
			if doc.root[0][1]:
				r = self.resolution.rewrite(path, doc.root[0])
				yield from render.chapter(r)

		yield "#!source\n"
		for x in itruncate(self.selectlines(element)):
			yield "\t" + x

	def r_element(self, path, element):
		"""
		# Emit a section containing the element's documentation.

		# The default switch target.
		"""
		yield self.newline
		yield self.section(0, None, path)

		doc = self.getdoc(path)

		# Retrieve the type of the element.
		resolve = self.resolution.partial(path)
		typdata = list(map(property_item, describe_type(resolve, element)))
		yield from self.r_control(element, documented=bool(doc), element=typdata)

		parameters = []
		try:
			for n in element[1]:
				if n and n[0] in {'parameter'}:
					parameters.append((n[2]['identifier'], n))
		except:
			del parameters[:]

		# Structure documentation and identify documented parameters.
		documented = set()
		if doc:
			r = doc.root[0]
			# Identify documentation relative to the element's path.
			prefix(path, r)

			# Join parameters.
			pd, docparams = section_items(doc, 'Parameters')
			# Clear and rebuild with joined data.
			pi = pd[1]
			del pi[:]
			for nid, p_documented, i in self.r_parameters(element, path, parameters, docparams):
				pi.append(i)
				if p_documented:
					documented.add(nid)
		else:
			# No documentation; empty chapter element.
			r = ('chapter', [], {})

		# Callable signature production.
		if element[0] not in {'property', 'data', 'field', 'import'}:
			# Only show required parameters and documented options.
			dparams = (
				# If the element provides an override syntax,
				# prefer it over the exact identifier.
				x[1][2].get('syntax', x[0]) for x in parameters
				if x[0] in documented or not x[1][2].get('optional', False)
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

	def switch(self, path, elements, *suffix):
		for x in elements:
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

	def selectlines(self, element):
		start, stop = element[2]['area']
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
		# Same factor project.
		return 'project-local'
	elif target.factor.container == origin.factor.container:
		# Same factor context.
		return 'context-local'
	else:
		# External. Use independent identifier.
		return 'remote'

def dr_absolute_path(requirements, context, project, reference):
	"""
	# Resolve an absolute reference.
	"""
	fpath = lsf.types.factor@reference
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
	cpath = project.factor.container

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
	path = lsf.types.factor@reference
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

def index(factor, deque=collections.deque, none={}):
	"""
	# Construct an index of elements using the identifier paths.
	"""
	subids = set(x[2].get('identifier') for x in factor[1])
	idx = {(): (factor, subids)}

	q = deque()
	q.extend(((), x) for x in factor[1])
	while q:
		# Process next queued element for indexing.
		prefix, element = q.popleft()
		try:
			element_id = element[2].get('identifier')
		except (KeyError, IndexError):
			continue
		else:
			if not element_id:
				continue

		# Descend into element's content by extending the queue.
		path = prefix + (element_id,)
		try:
			subids = set(x[2].get('identifier') for x in element[1])
		except IndexError:
			subids = set()
		subids.discard(None)
		idx[path] = (element, subids)
		q.extend((path, x) for x in element[1])

	return idx

def match(index, path, subpath):
	"""
	# Check for the presence of &subpath in the element identified by &path in &index.

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

		# Ascend
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
	def disambiguate(self, context, path, element, *suffix, AR=['reference', 'ambiguous']):
		assert element[0] in {'paragraph', 'key'}

		if isinstance(element[1], Paragraph):
			p = element[1]
		else:
			p = ipara(element)

		return p.__class__(
			(self.resolve(path, x) if x.typepath[:2] == AR else x)
			for x in p
		)

	# Anything that is guaranteed to not contain references.
	@comethod('syntax')
	@comethod('line')
	def reflect(self, context, path, element, *suffix):
		"""
		# Trap for elements where descent should not occur.
		"""
		return element[1]

	def switch(self, context, path, element, *suffix):
		subelements = element[1]

		for i, x in zip(range(len(subelements)), subelements):
			# Continue path when identifier is present.
			xid = x[2].get('identifier') or None
			if xid is not None:
				p = path + (xid,)
				subcontext = element
			else:
				p = path
				subcontext = context

			try:
				# Push context and overwrite elements.
				method = self.comethod(x[0], *suffix)
				# Reconstruct element with contents.
				subelements[i] = (x[0], method(subcontext, p, x)) + tuple(x[2:])
			except comethod.MethodNotFound:
				# Not directly rewritten.
				self.switch(subcontext, p, x, *suffix)

	def rewrite(self, context, root):
		"""
		# Rewrite the references in the element tree &root as relative IRI's.
		# [ Parameters ]
		# /context/
			# The identifier path of the documented element.
		# /root/
			# The documentation's chapter.
		"""
		self.switch(context, context, root)
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
			title, link, name_type, local = dr_context_path(
				self.context, self.project, reference.lstrip('.')
			)
		elif leading == 1:
			# Project Relative.
			title, link = dr_project_path(self.project, reference.lstrip('.'))
			local = 'project-local'
		else:
			if reference[:1] == '@':
				title, link, name_type, local = dr_absolute_path(
					self.requirements, self.context, self.project, reference[1:]
				)
			else:
				# Element Context Relative.
				local = 'factor-local'
				rpath = reference.split('.')
				targets = find(self.index, path, rpath)
				if targets:
					mdepth, prefix = targets[0]
					target = prefix + tuple(rpath[:mdepth])

					target_element = self.index[target][0]
					target_is_factor = target_element[2].get('factor') or None
					if target_is_factor:
						# The targeted element is potentially from a factor.
						target_path = target_element[2].get('path', [])
						target_relative = target_element[2].get('relative', 0)
						target_element_path = rpath[mdepth:]

						if target_relative:
							factor = ((self.project.factor // self.factor) ** target_relative) + target_path
						else:
							factor = self.factor.__class__.from_sequence(target_path)

						target_factor = list(factor.iterpoints())
						redirect = '.'.join(target_factor + target_element_path)
						absdata = dr_absolute_path(
							self.requirements, self.context, self.project, redirect
						)
						title, link, name_type, local = absdata
					else:
						name_type = target_element[0]
						if name_type == 'parameter':
							link = '#' + '.'.join(target[:-1]) + '.Parameters.' + target[-1]
						else:
							link = '#' + '.'.join(target)
						title = '[' + reference + ']'
				else:
					# No such element.
					local = 'invalid'
					link = "#{0}".format(reference.lstrip('.'))

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
		factorelement = load(f)
		resolution.add_index(factorelement)

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

	t = Text(resolution, factorelement, docs, data, source)
	return t.r_root(factorelement)
