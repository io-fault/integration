import typing
import itertools

from fault.context import tools
from fault.context import comethod

from fault.text import nodes
from fault.web import xml

from .tools import get_properties, interpret_property_fragment, interpret_properties

def formlink(reference:str) -> (str, str):
	"""
	# Construct a pair from the hyperlink reference string for constructing an anchor tag.

	# First element is the display text, second is the content for the `href` attribute.
	"""
	if reference.endswith(']'):
		# Explicit title.
		href, link_display = reference.rsplit('[', 1)
		link_display = link_display[:-1]

		# If it's only brackets, chances are it's an IPv6 IRI.
		# Handle this case by checking if the href is empty,
		# if it is, presume the brackets are the IRI.
		if not href.strip():
			href = reference
		if not link_display:
			link_display = reference
	else:
		# No explicit title.
		href = reference
		if href[:1] == '#':
			link_display = href[1:]
		else:
			link_display = href.lstrip('./')

	return (link_display, href)

def formtype(tree, element):
	"""
	# Construct HTML elements for representing a type given proper annotations.
	"""
	ts = None
	typdisplay = ()

	if ('type', 'syntax') in element:
		ts = element[('type', 'syntax')]
		typsyntax = tree.text(ts)
		typdisplay = typsyntax

	if ('type', 'reference') in element:
		# Override the output with the linked version.
		fragment = element[('type', 'reference')]
		rt, rs, *quals = fragment.type.split('/')
		typdisplay = tree.hyperlink(None, None, fragment.data, *quals, title=ts)

	return typdisplay

def load_control_value(value):
	if value[0] == 'paragraph':
		return nodes.document.export(value[1])

	if value[0] == 'set':
		# Presumes flag set.
		items = value[1]
		return list(map(nodes.document.export, (x[1][0][1] for x in value[1])))

	if value[0] == 'syntax':
		lines = [x[1][0] for x in value[1]]
		if not lines[-1].strip():
			del lines[-1:]
		return (value[-1].get('type'), lines)

def integrate(index, types, node):
	"""
	# Traverse the sections of the &node converting CONTEXT and CONTROL
	# admonition nodes into &node attributes.
	"""
	attr = node[2]
	subsect = []
	index[tuple(attr.get('absolute', ()) or ())] = (node, subsect)

	try:
		ftype, fnodes, fattr = node[1][0]
	except (LookupError, ValueError):
		# No elements at all
		pass
	else:
		if ftype == 'admonition' and fattr['type'] in types:
			meta = fattr['type'].lower()
			data = {
				k: load_control_value(v)
				for k, v in nodes.document.dictionary_pairs(fnodes[0][1])
			}
			attr[meta] = data
			del fnodes[:1]

		if 'control' in attr:
			ctl = attr['control']

			if 'reference' in ctl:
				attr['reference'] = ctl['reference']
			if 'title' in ctl:
				attr['title'] = ctl['title']
			if 'type' in ctl:
				attr['type'] = ctl['type'].sole[1]
			if 'flags' in ctl:
				attr['flags'] = set(x[0][1] for x in ctl['flags'])
			if 'element' in ctl:
				# Language level type/syntax, type/reference, etc.
				attr['element'] = dict(map(interpret_property_fragment, (
					x.sole for x in ctl['element']
				)))
				if ('source', 'area') in attr['element']:
					attr['area'] = map(int, attr['element'][('source', 'area')].split())
				#XXX if ('source', 'path') in attr['element']:

	for x in node[1]:
		if x[0] == 'section':
			sid = x[2].get('identifier', '')
			subsect.append(sid)
			integrate(index, types, x)

	return node

def prepare(chapter, path=(), types={'CONTROL', 'CONTEXT'}):
	# Prepare the chapter by relocating metadata nodes into preferred locations.

	idx = {}
	integrate(idx, types, chapter)

	if 'context' in chapter[-1]:
		ctx = chapter[-1]['context']
	else:
		ctx = chapter[-1]['context'] = {}

	if 'section-type' in ctx:
		ctx['section-type'] = ctx['section-type'].sole[1]
	else:
		ctx['section-type'] = 'unspecified'

	chapter[-1]['index'] = idx

	return idx, ctx

class Render(comethod.object):
	"""
	# Render an HTML document for the configured text document.
	"""

	@staticmethod
	@tools.cachedcalls(16)
	def slug(ident:str) -> str:
		# Clean identifier string for use with hyperlinks.
		# However, leave underscores alone.
		return None if ident is None else ident.replace(' ', '-')

	@classmethod
	@tools.cachedcalls(16)
	def steps(Class, path:typing.Sequence[str]):
		# Construct the absolute paths to each step in the path.
		prefixed = [path[0]]

		for p in path[1:]:
			p = Class.slug(p)
			prefixed.append(prefixed[-1] + '.' + p)

		return prefixed

	def __init__(self, output:xml.Serialization, context, prefix, depth, index, input:nodes.Cursor):
		self.context = context
		self.prefix = prefix
		self.depth = depth
		self.input = input
		self.index = index
		self.output = output

		# Shorthand
		self.element = output.element
		self.text = output.escape

	def default_resolver(self, capacity=16):
		return tools.cachedcalls(capacity)(self.comethod)

	def title(self, resolver, content, integrate, tag='h1'):
		return self.element(
			tag,
			itertools.chain(
				self.element('div', itertools.chain(
					self.element('div', self.text(''), ('class', 'left')),
					self.element('div', self.text(''), ('class', 'right')),
				), ('class', 'parallel')),
				self.element('span', self.text(''), ('class', 'prefix')),
				content,
			),
			('class', None if integrate == False else 'integrate')
		)

	def document(self, type, identifier, head=(), header=(), footer=(), resolver=None):
		"""
		# Render the HTML document from the given chapter.
		"""

		resolver = resolver or self.default_resolver()
		rnode, = self.input.root

		title = self.title(resolver,
			itertools.chain(
				self.element('span',
					self.text(identifier),
					('class', 'title'),
				),
				self.element('span',
					self.text(type),
					('class', 'factor-type'),
				),
			),
			False
		)

		return self.element('html',
			itertools.chain(
				head,
				self.element('body',
					itertools.chain(
						header,
						self.element('main',
							itertools.chain(
								title,
								self.root(resolver, rnode[1], rnode[-1]),
								self.element('h1', self.text(''), ('class', 'footing')),
							),
						),
						footer,
					)
				),
			),
		)

	def abstract(self, resolver, nodes, attr):
		"""
		# Extract the non-section content from the chapter.
		"""
		yield from self.element(
			'div',
			self.switch(resolver, nodes, attr),
			('class', "text.abstract")
		)

	def root(self, resolver, nodes, attr):
		chapter_content = list(itertools.takewhile((lambda x: x[0] != 'section'), nodes))
		yield from self.abstract(resolver, chapter_content, attr)
		yield from self.switch(resolver, nodes[len(chapter_content):], attr)

	@comethod('section')
	def semantic_section(self, resolver, nodes, attr, adjustment=0, tag='section'):
		ref = attr.get('reference', None)
		path = attr.get('absolute', ())
		if path is None:
			return
		documented = not ('undocumented' in attr.get('flags', ()))
		ttypes = {'text', 'subtext', 'unspecified'}
		ident = attr['identifier']
		typ = attr.get('type', self.context['section-type'])
		depth = len(path) + adjustment

		# Determine section integration.
		integrate = False
		if depth > adjustment:
			sl = attr.get('selector-level')
			sp = attr.get('selector-path')

			if sl is not None and sl > 0 and len(sp or (1,2)) == 1:
				integrate = True

		subcount = sum(1 for x in nodes if x[0] == 'section')
		htag = 'h1'
		leading = [(self.slug('.'.join(path[0:i+1])), path[i]) for i in range(depth - 1)]

		qpathstr = ('.'.join(x.replace(' ', '-') for x in path) if ident is not None else None)
		href = "#"+qpathstr

		# /title/ override present in CONTROL?
		if 'title' in attr:
			ptitle = self.paragraph(resolver, attr['title'], None)
		else:
			# Default to section identifier.
			ptitle = self.paragraph_content(resolver, [ident], None)

		element_properties = attr.get('element') or ()
		element_type = list(formtype(self, element_properties))
		if element_type:
			i_element_type = self.element('code',
				element_type,
				('class', 'type')
			)
		else:
			i_element_type = ()

		title = self.title(
			resolver,
			itertools.chain(
				itertools.chain.from_iterable([
					self.element('a',
						self.text(p[1]),
						('class', 'section'),
						href="#"+p[0]
					)
					for p in leading
				]) if attr['absolute'][0] != '' else (),
				self.element('a',
					ptitle,
					('class', 'title'),
					href = href
				),
				self.element('span',
					self.text(typ if typ not in ttypes else ''),
					('class', 'abstract-type'),
				),
				i_element_type,
			),
			integrate,
		)

		yield from self.element(
			tag,
			itertools.chain(
				title,
				self.reference_target(resolver, ref.sole[1]) if ref is not None else (),
				self.switch(resolver, nodes, attr)
			),
			('class', typ),
			('documented', str(documented).lower()),
			('local-identifier', ident),
			id=qpathstr
		)

	def reference_target(self, resolver, ref):
		"""
		# Display the target of the concept's reference.
		"""
		yield from self.element(
			'div',
			itertools.chain(
				self.element(
					'span',
					self.text(ref),
					('class', 'reference-display'),
				),
			),
			('class', 'subject-reference-display'),
		)

	def switch(self, resolver, nodes, attr):
		"""
		# Perform the transformation for the given node.
		"""
		for node in nodes:
			node[-1]['super'] = attr
			yield from resolver(node[0])(resolver, node[1], node[-1])

	@comethod('exception')
	def error(self, resolver, nodes, attr):
		yield from self.element('pre', self.text(str(nodes)))

	@comethod('syntax')
	def code_block(self, resolver, nodes, attr):
		lines = [x[1][0] + "\n" for x in nodes]
		if lines[-1] == "\n":
			ilines = itertools.islice(lines, 0, len(lines)-1)
		else:
			ilines = lines

		if attr['type'].startswith('/pl/'):
			cl = 'language-' + attr['type'][4:]
		else:
			cl = None

		yield from self.element('pre',
			self.element('code',
				self.text(''.join(ilines)),
				('class', cl)
			),
			('class', 'text.syntax'),
		)

	@comethod('paragraph')
	def normal_paragraph(self, resolver, nodes, attr):
		yield from self.element('p',
			self.paragraph_content(resolver, nodes, attr),
		)

	def list_item(self, resolver, item, attr):
		return self.switch(resolver, item, attr)

	@comethod('set')
	def ul_set(self, resolver, items, attr):
		yield from self.element(
			'ul',
			itertools.chain.from_iterable(
				self.element('li', self.list_item(resolver, i[1], i[-1]))
				for i in items
			),
			('class', "text.set")
		)

	@comethod('sequence')
	def ol_seq(self, resolver, items, attr):
		yield from self.element(
			'ol',
			itertools.chain.from_iterable(
				self.element('li', self.list_item(resolver, i[1], i[-1]))
				for i in items
			),
			('class', "text.sequence")
		)

	def dl_item_anchor(self, path):
		return self.element('a', (),
			('class', 'dkn'),
			('href', "#" + self.slug(".".join(path))),
		)

	def dl_key_identifier(self, kpg):
		for typ, data in kpg:
			if typ == 'reference/hyperlink' or typ.startswith('reference/hyperlink/'):
				if data[-1:] == ']':
					# Use title.
					yield data.rsplit('[', 1)[1][:-1]
				else:
					if data[:1] == '#':
						yield data[1:]
					else:
						yield data
			else:
				yield data

	def dl_item(self, resolver, item, attr, sattr, prefix):
		item_properties = {}
		k, v = item
		kp = nodes.document.export(k[1])
		kpi = ''.join(self.dl_key_identifier(kp))
		iclass = None
		attr['super'] = sattr
		attr['absolute'] = (sattr['absolute'] or ()) + (kpi,)

		pset = get_properties(v[1])
		if pset:
			# First node was a property set.
			del v[1][0:1]
			item_properties.update(pset.items())

		documented = True
		typannotation = ()

		if len(kp) == 1:
			# Parameter case.
			sole = kp[0]
			soletype, subtype, *cast = sole.type.split('/')

			if cast and cast[0] in {'parameter', 'field', 'constant'}:
				iclass = cast[0]

				typdata = list(formtype(self, item_properties))
				if typdata:
					typannotation = self.element(
						'code', typdata, ('class', 'type')
					)
				else:
					typannotation = ()

				# Check for not-documented literal.
				try:
					vp = nodes.document.export(v[1][0][1])
					if vp[0].type.endswith('/ctl/absent'):
						documented = False
				except:
					pass
		else:
			sole = None
			soletype = None
			cast = ()

		return self.element('div',
			itertools.chain(
				self.element('dt',
					itertools.chain(
						self.dl_item_anchor(attr['absolute']),
						self.paragraph_content(resolver, k[1], attr),
						typannotation,
					),
				),
				self.element('dd', self.switch(resolver, v[1], attr)),
			),
			('id', self.slug(prefix(kpi))),
			('class', iclass),
			('documented', str(documented).lower())
		)

	@comethod('dictionary')
	def dl_dict(self, resolver, items, attr):
		p = attr['super']
		if p is not None:
			p = p.get('absolute', None)

		if p is not None:
			prefix = ('.'.join(p) + '.').__add__
			attr['absolute'] = tuple(p)
		else:
			prefix = (lambda x: None)
			attr['absolute'] = None

		yield from self.element(
			'dl',
			itertools.chain.from_iterable(
				self.dl_item(resolver, i[1], i[-1], attr, prefix)
				for i in items
			),
			('class', "text.mapping")
		)

	def admonition_table(self, resolver, icon, severity, content):
		el = self.element
		ch = itertools.chain

		icon = el('span', (), ('class', "admonition.icon"))
		sev = el('span', self.text(severity), ('class', "admonition.severity"))

		c = self.switch(resolver, content, None)
		main = el('div', c, ('class', "admonition.content"))

		return el('table',
			ch(
				el('tr', ch(el('td', icon), el('td', sev))),
				el('tr', ch(el('td', ()), el('td', main))),
			),
		)

	@comethod('admonition')
	def block_admonition(self, resolver, content, attr):
		if not content:
			return

		typ = attr['type']
		if typ in {'CONTROL', 'CONTEXT'}:
			return

		if typ == 'INHERIT':
			yield from self.element('div',
				self.element('code',
					formtype(self, dict(interpret_properties(content[0][1]))),
					('class', 'type'),
				),
				('class', 'inheritance'),
			)
			return

		severity = 'admonition-' + typ

		yield from self.element(
			'div',
			self.admonition_table(resolver, (), attr['type'], content),
			('class', severity)
		)

	def link(self, eclass, content, href, tag='a'):
		return self.element(
			tag,
			itertools.chain(
				content,
				self.element('span', self.text(""), ('class', 'ern')),
			),
			('class', eclass),
			href = href
		)

	@comethod('reference', 'section')
	def dereference_section(self, resolver, context, text, *quals):
		yield from self.link(
			'section-reference',
			self.text(text),
			"#" + self.slug(text),
		)

	@comethod('reference', 'ambiguous')
	def dereference_ambiguous(self, resolver, context, text, *quals):
		# Most references are expected to be rewritten as hyperlinks.
		# However, this case should be handled.
		yield from self.link(
			(quals and quals[0] or None),
			self.text(text),
			href = text,
		)

	@comethod('reference', 'hyperlink')
	def hyperlink(self, resolver, context, text, *quals, title=None):
		link_display, href = formlink(text)
		link_content_text = self.text(title or link_display)
		link_content = link_content_text

		link_class = 'absolute'
		link_target_type = None
		if quals:
			# First cast segment past reference/hyperlink
			# identifies the anchor class.
			link_class = quals[0]

			# If there's a subtype, add a span.
			if quals[1:2]:
				link_target_type = quals[1]
				link_content = self.element('span',
					link_content_text,
					('class', link_target_type),
				)

		if link_class == 'project-local':
			depth = self.depth
			if link_target_type == 'project-name':
				# self-reference; essentially treat as context-local
				if self.prefix and href.startswith(self.prefix):
					href = href[len(self.prefix):]
			else:
				depth -= 1
		elif link_class == 'context-local':
			# Consistent.
			depth = self.depth

			# Remove prefix from link only if one is configured.
			if self.prefix and href.startswith(self.prefix):
				href = href[len(self.prefix):]
		else:
			# Unrecognized relation.
			# Either factor local or absolute.
			depth = 0

		yield from self.element(
			'a',
			link_content,
			('class', link_class),
			href = ('../' * depth if href[:1] != '#' else '') + href
		)

	@comethod('text', 'normal')
	def normal_text(self, resolver, context, text, *quals):
		yield from self.element(
			'span',
			self.text(text),
			('class', ".".join(("text.normal",) + quals)),
		)

	@comethod('text', 'line-break')
	def line_break(self, resolver, context, text, *quals):
		yield from self.element(
			'span',
			self.text(text),
			('class', "text.line-break"),
		)

	@comethod('text', 'emphasis')
	def emphasized_text(self, resolver, context, text, level):
		level = int(level) #* Invalid emphasis level normally from &fault.text.types.Paragraph

		if level < 1:
			cl = "text.normal"
		elif level < 2:
			cl = "text.emphasis"
		else:
			cl = "text.emphasis.heavy"

		yield from self.element(
			'span',
			self.text(text),
			('class', cl),
		)

	@comethod('literal', 'grave-accent')
	def inline_literal(self, resolver, context, text, *quals):
		yield from self.element(
			'code',
			self.text(text),
			('class', '.'.join(quals)),
		)

	def paragraph_content(self, resolver, content, attr):
		yield from self.paragraph(resolver, nodes.document.export(content), attr)

	def paragraph(self, resolver, para, attr):
		for pt in para:
			qual, txt = pt
			typ, subtype, *local = qual.split('/')

			# Filter void zones.
			if len(local) == 1 and local[0] == 'void':
				continue

			yield from self.comethod(typ, subtype)(resolver, attr, txt, *local)

	def subtext(self, resolver, snodes, attr):
		"""
		# Currently unused.

		# Originally, this parsed the syntax node content as kleptic text.
		# Eventually &.join was changed to integrate the documentation into
		# the generated sections leaving this unused.
		"""
		text = '\n'.join(x[1][0] for x in snodes[0][1])

		sub = nodes.Cursor.from_chapter_text(text)
		sub.filters['titled'] = (lambda x: bool(x[-1].get('identifier')))

		# Build section index and assign paths.
		r, = sub.root

		# Prefix with empty path.
		r[-1]['absolute'] = ()
		idx, ctx = prepare(r)
		for v, subs in idx.values():
			a = v[2]['absolute']
			a = ('',) + tuple(a or ())
			v[2]['absolute'] = a

		# Module abstract.
		chapter_content = list(itertools.takewhile((lambda x: x[0] != 'section'), r[1]))
		yield from self.abstract(resolver, chapter_content, attr)

		for snode in sub.select("/section"):
			yield from self.semantic_section(resolver, snode[1], snode[-1], tag='article')

def transform(prefix, depth, chapter, styles=[], identifier='', type=''):
	c = nodes.Cursor.from_chapter_text(chapter)
	sx = xml.Serialization(xml_encoding='utf-8')
	r, = c.root
	idx, ctx = prepare(r)
	rhtml = Render(sx, ctx, prefix, depth, idx, c)
	head = rhtml.element('head',
		itertools.chain(
			rhtml.element('meta', None, charset='utf-8'),
			itertools.chain.from_iterable(
				rhtml.element('link', (), rel='stylesheet', href=x)
				for x in styles
			)
		),
	)
	return rhtml.document(type, identifier, head=head)
