import typing
import itertools

from fault.context import tools
from fault.context import comethod

from fault.text import nodes
from fault.web import xml

def integrate(index, types, node, default_type='text'):
	# Traverse the sections of the &tree converting CONTEXT and CONTROL
	# admonition nodes into attributes.
	subsect = []
	index[tuple(node[2].get('absolute', ()) or ())] = (node, subsect)

	sub = []
	for x in node[1][:4]:
		if x[0] == 'admonition' and x[-1]['type'] in types:
			meta = x[2]['type'].lower()
			data = {
				k: nodes.document.export(v[1])
				for k, v in nodes.document.dictionary_pairs(x[1][0][1])
			}
			node[2][meta] = data
		else:
			sub.append(x)

	if 'control' in node[2]:
		ctl = node[2]['control']

		if 'type' in ctl:
			node[2]['type'] = ctl['type'].sole[1]

	# Remove the now integrated data.
	node[1][:4] = sub

	for x in node[1]:
		if x[0] == 'section':
			x[2]['type'] = default_type
			sid = x[2].get('identifier', '')
			subsect.append(sid)
			integrate(index, types, x, default_type=default_type)

	return node

def prepare(chapter, path=(), types={'CONTROL', 'CONTEXT'}, default_type='text'):
	# Prepare the chapter by relocating metadata nodes into preferred locations.

	idx = {}
	integrate(idx, types, chapter, default_type=default_type)

	# CONTEXT is actually chapter/document metadata.
	# Relocate the context dictionary into the root node.
	ctx = chapter[1][0][-1].pop('context', None)

	chapter[-1]['context'] = ctx
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

	def __init__(self, output:xml.Serialization, index, input:nodes.Cursor):
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
				self.element('span', self.text(''), ('class', 'prefix')),
				content,
			),
			('class', None if integrate == False else 'integrate')
		)

	def document(self, identifier, head=(), header=(), footer=(), resolver=None):
		"""
		# Render the HTML document from the given chapter.
		"""

		resolver = resolver or self.default_resolver()
		rnode, = self.input.root

		return self.element('html',
			itertools.chain(
				head,
				self.element('body',
					itertools.chain(
						header,
						self.element('main',
							itertools.chain(
								self.title(resolver, self.text(identifier), False),
								self.root(resolver, rnode[1], rnode[-1]),
							),
						),
						footer,
					)
				),
			),
		)

	def root(self, resolver, nodes, attr):
		default_section = nodes[0]

		if len(default_section[1]) > 0 and default_section[1][0][0] == 'syntax':
			yield from self.subtext(resolver, default_section[1], default_section[-1])
		else:
			yield from self.abstract(resolver, nodes[0][1], nodes[0][-1])

		yield from self.switch(resolver, nodes[1:], attr)

	@comethod('section')
	def semantic_section(self, resolver, nodes, attr, adjustment=0, tag='section'):
		ttypes = {'text', 'subtext', 'unspecified'}
		ident = attr['identifier']
		path = attr.get('absolute', ())
		typ = attr.get('type', 'unspecified')
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

		# Scan for title override.
		for node in nodes[:4]:
			if node[0] == 'admonition' and node[-1]['type'] == 'TITLE':
				title = self.title(
					resolver,
					self.element('a',
						self.paragraph_content(resolver, node[1], None),
						('class', 'title'),
						href = href,
					),
					integrate,
				)
				break
		else:
			title = self.title(
				resolver,
				itertools.chain(
					itertools.chain.from_iterable([
						self.element('a', self.text(p[1]),
							('class', 'section'),
							href="#"+p[0]
						)
						for p in leading
					]) if attr['absolute'][0] != '' else (),
					self.element('a',
						self.paragraph_content(resolver, [ident], None),
						('class', 'title'),
						href = href
					),
					self.element('span',
						self.text(typ if typ not in ttypes else ''),
						('class', 'abstract-type'),
					),
				),
				integrate,
			)

		yield from self.element(
			tag,
			itertools.chain(
				title,
				self.switch(resolver, nodes, attr)
			),
			('class', typ),
			id=qpathstr
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
		yield from self.element('pre', self.text("error"))

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

	def dl_item(self, resolver, item, attr, sattr, prefix):
		k, v = item
		kp = ''.join(x[1] for x in nodes.document.export(k[1]))
		attr['super'] = sattr
		attr['absolute'] = sattr['absolute'] + (kp,)

		return itertools.chain(
			self.element('dt',
				itertools.chain(
					self.dl_item_anchor(attr['absolute']),
					self.paragraph_content(resolver, k[1], attr),
				),
				id=self.slug(prefix(kp)),
			),
			self.element('dd', self.switch(resolver, v[1], attr)),
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
		lead = content[0]
		severity = 'admonition-' + attr['type']

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
		yield from self.link(
			(quals and quals[0] or None),
			self.text(text),
			href = text,
		)

	@comethod('reference', 'hyperlink')
	def hyperlink(self, resolver, context, text, *quals):
		yield from self.element(
			'a',
			self.text(quals and ' '.join(quals) or text),
			('class', 'absolute'),
			href = text
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
		p = nodes.document.export(content)

		for pt in p:
			qual, txt = pt
			typ, subtype, *local = qual.split('/')

			# Filter void zones.
			if len(local) == 1 and local[0] == 'void':
				continue

			yield from self.comethod(typ, subtype)(resolver, attr, txt, *local)

	def abstract(self, resolver, nodes, attr):
		"""
		# Extract the non-section content of the default section.
		"""
		nn = (node for node in nodes if node[0] != 'section')

		yield from self.element(
			'div',
			self.switch(resolver, nn, attr),
			('class', "text.abstract")
		)

	def subtext(self, resolver, snodes, attr):
		text = '\n'.join(x[1][0] for x in snodes[0][1])

		sub = nodes.Cursor.from_chapter_text(text)
		sub.filters['titled'] = (lambda x: bool(x[-1].get('identifier')))

		# Build section index and assign paths.
		r, = sub.root

		# Prefix with empty path.
		r[-1]['absolute'] = ()
		idx, ctx = prepare(sub.root[0], default_type='subtext')
		for v, subs in idx.values():
			a = v[2]['absolute']
			a = ('',) + tuple(a or ())
			v[2]['absolute'] = a

		# Module abstract.
		inodes = sub.select("/section[]/*")
		attr = sub.select("/section[]#1")[0][-1]
		yield from self.abstract(resolver, inodes, attr)

		for snode in sub.select("/section?titled"):
			yield from self.semantic_section(resolver, snode[1], snode[-1], tag='article')

def transform(chapter, styles=[], identifier=''):
	c = nodes.Cursor.from_chapter_text(chapter)
	sx = xml.Serialization(xml_encoding='utf-8')
	r, = c.root
	idx, ctx = prepare(r)
	rhtml = Render(sx, idx, c)
	head = rhtml.element('head',
		itertools.chain(
			itertools.chain.from_iterable(
				rhtml.element('link', (), rel='stylesheet', href=x)
				for x in styles
			)
		),
	)
	return rhtml.document(identifier, head=head)
