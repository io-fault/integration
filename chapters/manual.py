"""
# mdoc rendering for text element trees.
"""
import sys
import typing
import itertools
import collections

from fault.context import tools
from fault.context import comethod
from fault.text import nodes
from fault.system import files

from .tools import get_properties, interpret_property_fragment, interpret_properties
from .html import prepare

escape_characters = {
	"'": "\\[aq]",
	"`": "\\*(ga",
	'"': "\\*q",
	"\\": "\\[char92]",
}

def escape(string:str, table=str.maketrans(escape_characters), quote='"') -> str:
	"""
	# Escape text for use as macro arguments.
	"""
	if not string or len(string) == 2:
		# In certain contexts, notably `.It`, even a quoted
		# form may be interpreted as a macro. So, when
		# the desired escape subject is the size of
		# a macro name, prefix it with the zero-width
		# space to discourage interpretation.
		qstart = quote + '\\&'
	else:
		qstart = quote

	return qstart + string.translate(table) + quote

def _form(*fields) -> str:
	return " ".join(fields)

literal_casts = {
	'library': '.Lb',
	'include': '.In',
	'literal': '.Li',
	'environ': '.Ev',
	'errno': '.Er',
	'internal-command': '.Ic',
	'path': '.Pa',
	'function': '.Fn',
	'default': '.Ql',
	'argument': '.Fa',
	'function': '.Fn',
	'function-type': '.Ft',
	'type': '.Vt',
	'variable': '.Va',
	'const': '.Dv',
	'flag': '.Fl',
	'author': '.An',
	'tradename': '.Tn',
	'memory-address': '.Ad',
	'standard': '.St',
	'mdoc-comment': '.\\"',
}

def trim_option_flag(opt):
	"""
	# Eliminate redundant slugs for mdoc macros and identify join.
	"""
	if opt == '-:':
		# Handle allowed exception for cases where a colon is an option.
		return (':', False)

	if (opt[:2] == '--' and opt[-1:] == '='):
		end = None
		join = True
	elif opt[-1:] == ':':
		end = -1
		join = True
	else:
		end = None
		join = False

	return opt[1:end], join

class Render(comethod.object):
	"""
	# Render an HTML document for the configured text document.
	"""

	def __init__(self, output, context, prefix, index, input:nodes.Cursor, relation):
		self.context = context
		self.prefix = prefix
		self.input = input
		self.index = index
		self.output = output
		self.relation = relation

		# Shorthand
		self.element = _form
		self.text = escape

	def default_resolver(self, capacity=16):
		return tools.cachedcalls(capacity)(self.comethod)

	def document(self, type, identifier, resolver=None):
		"""
		# Render the manual document from the given chapter.
		"""

		resolver = resolver or self.default_resolver()
		rnode, = self.input.root
		context = rnode[-1]['context']

		t = rnode[-1]['context']['title'].sole.data.upper()
		heading = [
			self.text(context[x].sole.data) for x in (
				'title', 'section', 'volume'
			)
		]

		for line in self.context.get('comment', (None, ()))[1]:
			yield self.element('.\\"', line)

		yield self.element('.Dd', self.text(context['date'].sole.data))
		yield self.element('.Dt', *heading)
		yield self.element('.Os', self.text(context['system'].sole.data))

		yield from self.root(resolver, rnode[1], rnode[-1])

	def root(self, resolver, nodes, attr):
		# Currently discarded.
		for v in nodes:
			if v[0] != 'section':
				# Ignore non-section chapter content.
				continue

			if v[-1]['identifier'] == 'NAME':
				stype = v[-1]['identifier'].lower()
			elif v[-1]['identifier'] == 'SYNOPSIS':
				if self.relation:
					stype = self.relation + '-synopsis'
				else:
					stype = 'synopsis'
			else:
				stype = 'chapter'

			v[-1]['s-type'] = stype
			yield from resolver('section', stype)(resolver, v[1], v[-1])

	@comethod('section', 'name')
	def name_section(self, resolver, nseq, attr):
		names = attr.get('names', ())
		if not names:
			# Presumably, this is not a normal manual page.
			yield from self.semantic_section(resolver, nseq, attr)
			return

		yield self.element('.Sh', 'NAME')
		*sepnames, _ = tools.interlace(names, itertools.repeat(' , '))
		yield self.element('.Nm', *sepnames)

		yield self.element('.Nd')
		yield from self.switch(resolver, nseq, attr)

	@comethod('section', 'options-synopsis')
	def command_synopsis_section(self, resolver, nseq, attr):
		yield self.element('.Sh', 'SYNOPSIS')
		yield from self.switch(resolver, nseq, attr)

		names = attr['names']
		fields = attr['fields']
		options = attr['options']

		for name in names:
			yield self.element('.Nm', self.text(name))

			for (fname, optlist) in options[name]:
				args = fields.get(fname, ())
				args = [x.sole.data for x in args]
				if not args:
					# Flag set.
					for opt in optlist:
						yield self.element('.Op', 'Fl', self.text(opt[1:]))
				else:
					# Parameterized option. Use primary for synopsis.
					argstr = ' Ar '.join(args)
					if not optlist:
						yield self.element('.Ar', argstr)
					else:
						opt = optlist[0]
						optstr, join = trim_option_flag(opt)
						if join:
							yield self.element('.Op', 'Fl', optstr, 'Ns', 'Ar', argstr)
						else:
							yield self.element('.Op', 'Fl', optstr, 'Ar', argstr)

	@comethod('section', 'parameters-synopsis')
	def function_synopsis_section(self, resolver, nseq, attr):
		yield self.element('.Sh', 'SYNOPSIS')
		yield from self.switch(resolver, nseq, attr)

		names = attr['names']
		types = attr['types']
		fields = attr['fields']
		options = attr['options']

		for name, typ in zip(names, types):
			yield self.element('.Ft', self.text(typ))
			yield self.element('.Fo', self.text(name))

			for (fname, optlist) in options[name]:
				args = fields.get(fname, ())
				for a in args:
					yield self.element('.Fa', self.text(a.sole.data))

			yield self.element('.Fc')

	@comethod('section')
	def subsection(self, resolver, nodes, attr):
		yield self.element('.Ss', attr['identifier'])
		yield from self.switch(resolver, nodes, attr)

	@comethod('section', 'synopsis')
	@comethod('section', 'chapter')
	def semantic_section(self, resolver, nodes, attr):
		yield self.element('.Sh', attr['identifier'])
		yield from self.switch(resolver, nodes, attr)

	def switch(self, resolver, nodes, attr):
		"""
		# Perform the transformation for the given node.
		"""
		for i, node in enumerate(nodes):
			node[-1]['super'] = attr
			node[-1]['index'] = i
			yield from resolver(node[0])(resolver, node[1], node[-1])

	@comethod('syntax')
	def code_block(self, resolver, nodes, attr):
		if nodes[-1][1][0].strip() == '':
			del nodes[-1:]

		for line in (x[1][0] for x in nodes):
			yield self.element('.Dl', self.text(line))

	@comethod('paragraph')
	def normal_paragraph(self, resolver, nodes, attr):
		if attr.get('index', -1) != 0:
			# Ignore initial paragraphs breaks in sequences.
			yield self.element('.Pp')
		yield from self.paragraph_content(resolver, nodes, attr)

	def sequencing(self, type, resolver, items, attr):
		yield self.element('.Bl', type, '-compact')

		for i in items:
			yield self.element('.It', 'Ns')
			yield from self.switch(resolver, i[1], attr)

		yield self.element('.El')

	@comethod('set')
	def unordered(self, resolver, items, attr):
		return self.sequencing('-dash', resolver, items, attr)

	@comethod('sequence')
	def ordered(self, resolver, items, attr):
		return self.sequencing('-enum', resolver, items, attr)

	@comethod('mapping', 'key')
	def paragraph_key(self, resolver, items, attr):
		macros = self.paragraph(resolver, nodes.document.export(items), attr)
		yield self.element('.It', *(x[1:] for x in macros))

	@comethod('mapping', 'option-case')
	def options_record(self, resolver, items, attr):
		"""
		# Format the (id)`option-case` element substituted by &join_synopsis_details.
		"""
		arglist = attr['arguments']
		optlist = attr['options']

		if not arglist:
			# Options only. Flag set.
			flags = ' Fl '.join(self.text(x[1:]) for x in optlist)
			yield self.element('.It', 'Fl', flags)
		elif not optlist:
			# Arguments only.
			args = ' Ar '.join(self.text(x) for x in optlist)
			yield self.element('.It', 'Ar', args)
		else:
			# Options taking arguments.
			args = ' Ar '.join(self.text(x.sole.data) for x in arglist)
			for opt in optlist:
				opt, join = trim_option_flag(opt)
				if join:
					# Visually joined.
					yield self.element('.It', 'Fl', opt, 'Ns', 'Ar', args)
				else:
					# Visually separated.
					yield self.element('.It', 'Fl', opt, 'Ar', args)

	@comethod('mapping', 'parameter-case')
	def parameter_record(self, resolver, items, attr):
		"""
		# Format the (id)`parameter-case` element substituted by &join_synopsis_details.
		"""
		arglist = attr['arguments']
		argtext = (self.text(a.sole.data) for a in arglist)
		*args, _ = tools.interlace(argtext, itertools.repeat(' , '))
		yield self.element('.It', 'Fa', *args)

	@comethod('dictionary')
	def mapping(self, resolver, items, attr):
		yield self.element('.Bl', "-tag -width indent")

		for pair in items:
			assert pair[0] == 'item'

			ki = pair[-1]['identifier']
			k, c = pair[1]
			yield from resolver('mapping', k[0])(resolver, k[1], k[-1])
			yield from self.switch(resolver, c[1], c[-1])

		yield self.element('.El')

	@comethod('admonition')
	def block_admonition(self, resolver, content, attr):
		if not content:
			return

		typ = attr['type']
		if typ in {'CONTROL', 'CONTEXT'}:
			return

		# Force paragraph break and indent content.
		yield self.element('.Pp')
		yield self.element('.Em', self.text(typ), 'Ns')
		yield self.element('.No', ':')
		yield self.element('.Bd', "-filled", "-offset indent")
		yield from self.switch(resolver, content, attr)
		yield self.element('.Ed')

	@comethod('reference', 'section')
	def reference_section(self, resolver, context, text, *quals):
		return self.element('.Sx', self.text(text), 'Ns')

	@comethod('reference', 'ambiguous')
	def reference_ambiguous(self, resolver, context, text, *quals):
		# Most references are expected to be rewritten as hyperlinks.
		# However, this case should be handled.
		if text[-1:].isdigit() and text[-2] == '.':
			name, sect = text.rsplit('.', 1)
			return self.element('.Xr', self.text(name), str(sect), 'Ns')

		return self.element('.Aq', self.text(text), 'Ns')

	@comethod('reference', 'hyperlink')
	def reference_hyperlink(self, resolver, context, text, *quals, title=None):
		link_display, href = formlink(text)
		link_content_text = self.text(title or link_display)
		return self.element('.Lk', self.text(href), link_content_text, 'Ns')

	@comethod('text', 'normal')
	def normal_text(self, resolver, context, text, *quals):
		return self.element('.No', self.text(text), 'Ns')

	@comethod('text', 'line-break')
	def line_break(self, resolver, context, text, *quals):
		if text:
			return self.element('.Ns', '"\\&"')
		else:
			return '.'

	@comethod('text', 'emphasis')
	def emphasized_text(self, resolver, context, text, level):
		level = int(level) #* Invalid emphasis level normally from &fault.text.types.Paragraph

		if level < 1:
			return self.normal_text(resolver, context, text)
		elif level < 2:
			return self.element('.Sy', self.text(text), 'Ns')
		else:
			return self.element('.Em', self.text(text), 'Ns')

	@comethod('literal', 'grave-accent')
	def inline_literal(self, resolver, context, text, *quals):
		cast = quals[0] if quals else 'default'
		if cast == 'mdoc-comment':
			return ' '.join((literal_casts[cast], text))
		else:
			macro = literal_casts.get(cast, 'Ql')
			return self.element(macro, self.text(text), 'Ns')

	def paragraph_content(self, resolver, content, attr):
		yield from self.paragraph(resolver, nodes.document.export(content), attr)

	def paragraph(self, resolver, para, attr):
		for pt in para:
			qual, txt = pt
			typ, subtype, *local = qual.split('/')

			# Filter void zones.
			if len(local) == 1 and local[0] == 'void':
				continue

			yield resolver(typ, subtype)(resolver, attr, txt, *local)

def split_option_flags(p):
	"""
	# Retrieve the reference and any leading option fields.
	"""

	*leading, ref = p
	if ref.type.startswith('reference/'):
		ref = ref.data # Identifier in OPTIONS or PARAMETERS.
	else:
		# Not a reference. Presume option.
		leading.append(ref)
		ref = None

	if leading:
		leading = list(map(str.strip, itertools.chain(*[x.data.split() for x in leading])))

	return ref, leading

def _pararefs(n):
	n = n[1][1][1][0][1]
	for i in n:
		p = nodes.document.export(i[1][0][1])
		yield p #* Not a sole reference.

def recognize_synopsis_options(section):
	e = None
	for si, e in enumerate(section):
		if e[0] == 'dictionary':
			del section[si:si+1]
			break
	else:
		return []

	return [
		(i[-1]['identifier'],
			nodes.document.export(i[1][0][1]).sole.type.split('/')[-1],
			list(map(split_option_flags, _pararefs(i)))
		)
		for i in e[1]
	]

def join_synopsis_details(context, index, synsect='SYNOPSIS'):
	if ('OPTIONS',) in index:
		relation = 'OPTIONS'
		case_id = 'option-case'
	elif ('PARAMETERS',) in index:
		relation = 'PARAMETERS'
		case_id = 'parameter-case'
	else:
		return None

	syn, _ = index[(synsect,)] #* No SYNOPSIS?
	synopts = recognize_synopsis_options(syn[1])

	fields = {}
	# Get ordered list of names.
	names = []
	types = []
	# Parameter list for each name.
	optlists = collections.defaultdict(list)
	# The option set for each option reference.
	optindex = {}

	for subjname, typ, options in synopts:
		names.append(subjname)
		types.append(typ)
		optlists[subjname].extend(options)
		for optref, optset in options:
			optindex[optref] = optset

	if not names:
		names = [p.sole.data for p in context['names']]

	if ('NAME',) in index:
		index[('NAME',)][0][-1]['names'] = names

	xrs, _ = index[(relation,)] #* Missing OPTIONS/PARAMETERS?
	for node in xrs[1]:
		if node[0] != 'dictionary':
			continue

		# First dictionary, structure synopsis.
		for i in node[1]:
			# Name and Parameter/Option list.
			key, value = i[1]

			refname = i[-1]['identifier']

			if value[1][0][0] == 'sequence':
				argpara = (i[1][0] for i in value[1][0][1])
				arglist = [
					nodes.document.export(x[1])
					for x in argpara
				]
				del value[1][:1]
			else:
				# Likely option set.
				arglist = []

			fields[refname] = arglist

			struct = {
				'identifier': refname,
				'arguments': arglist,
				'options': optindex.get(refname, refname.split()),
			}

			# Replace the key with an easily identified element
			# for customized processing of the synopsis' name mapping.
			i[1][0] = (case_id, [], struct)
		break
	else:
		# No dictionary in found.
		raise Exception("synopsis reference section contained no dictionary")

	syn[-1]['names'] = names
	syn[-1]['types'] = types
	syn[-1]['options'] = optlists
	syn[-1]['fields'] = fields

	return relation

def transform(prefix, chapter, identifier='', type=''):
	c = nodes.Cursor.from_chapter_text(chapter)
	r, = c.root
	idx, ctx = prepare(r)
	rel = join_synopsis_details(ctx, idx)
	man = Render(None, ctx, prefix, idx, c, rel.lower())
	return man.document(type, identifier)
