"""
# mdoc rendering for text element trees.
"""
import sys
import typing
import itertools
import collections

from fault.system import files
from fault.context import tools
from fault.context import comethod

from fault.text.io import structure_chapter_text, structure_paragraph_element
from fault.text.document import export as iparagraph
from .query import Cursor, navigate
from .html import prepare, formlink

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
	'default': '.Ql',
	'library': '.Lb',
	'include': '.In',
	'literal': '.Li',
	'environ': '.Ev',
	'errno': '.Er',
	'internal-command': '.Ic',
	'memory-address': '.Ad',
	'path': '.Pa',
	'function': '.Fn',
	'function-type': '.Ft',
	'function-argument': '.Fa',
	'variable-type': '.Vt',
	'variable': '.Va',
	'const': '.Dv',
	'option-flag': '.Fl',
	'option-argument': '.Ar',
	'optional': '.Op',
	'author': '.An',
	'tradename': '.Tn',
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

	def __init__(self, output, context, prefix, index, input:Cursor, relation):
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
		relement, = self.input.root
		context = relement[-1]['context']

		t = relement[-1]['context']['title'].sole.data.upper()
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

		yield from self.root(resolver, relement[1], relement[-1])

	def root(self, resolver, elements, attr):
		# Currently discarded.
		for v in elements:
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

			yield self.element('.Bk')
			for (fname, optlist) in options[name]:
				args = fields.get(fname, ())
				if not args:
					# Flag set.
					for opt in optlist:
						yield self.element('.Op', 'Fl', self.text(opt[1:]))
				else:
					# Parameterized option. Use primary for synopsis.
					if not optlist:
						yield from self.format_option_arguments(args)
					else:
						argstr = ' '.join(x[1:] for x in self.format_option_arguments(args))
						opt = optlist[0]
						optstr, join = trim_option_flag(opt)
						if join:
							yield self.element('.Op', 'Fl', optstr, 'Ns', argstr)
						else:
							yield self.element('.Op', 'Fl', optstr, argstr)
			yield self.element('.Ek')

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
	def subsection(self, resolver, elements, attr):
		yield self.element('.Ss', attr['identifier'])
		yield from self.switch(resolver, elements, attr)

	@comethod('section', 'synopsis')
	@comethod('section', 'chapter')
	def semantic_section(self, resolver, elements, attr):
		yield self.element('.Sh', attr['identifier'])
		yield from self.switch(resolver, elements, attr)

	def switch(self, resolver, elements, attr):
		"""
		# Perform the transformation for the given element.
		"""
		for i, element in enumerate(elements):
			element[-1]['super'] = attr
			element[-1]['index'] = i
			yield from resolver(element[0])(resolver, element[1], element[-1])

	@comethod('syntax')
	def code_block(self, resolver, elements, attr):
		if elements[-1][1][0].strip() == '':
			del elements[-1:]

		lines = (x[1][0] for x in elements)

		if attr['type'] == 'comment':
			for line in lines:
				yield self.element('.\\"', line)
		else:
			for line in lines:
				yield self.element('.Dl', self.text(line))

	def sequencing(self, type, resolver, items, attr):
		yield self.element('.Bl', type, '-compact')

		if type in {'-dash', '-enum'}:
			end = ()
		else:
			end = ('Ns',)

		for i in items:
			yield self.element('.It', *end)
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
		macros = self.paragraph(resolver, items, attr)
		yield self.element('.It', *(x[1:] for x in macros))

	def format_option_arguments(self, arglist):
		for x in arglist:
			f = x.sole

			if f.type.endswith('/optional'):
				yield self.element('.Op', 'Ar', self.text(f.data))
			else:
				yield self.element('.Ar', self.text(f.data))

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
			yield self.element('.It', 'Xo')
			yield from self.format_option_arguments(arglist)
			yield self.element('.Xc')
		else:
			# Options taking arguments.
			args = ' '.join(self.format_option_arguments(arglist))
			for opt in optlist:
				opt, join = trim_option_flag(opt)
				if join:
					# Visually joined.
					yield self.element('.It', 'Fl', opt, 'Ns', 'Xo')
					yield from self.format_option_arguments(arglist)
				else:
					# Visually separated.
					yield self.element('.It', 'Fl', opt, 'Xo')
					yield from self.format_option_arguments(arglist)
				yield self.element('.Xc')

	@comethod('mapping', 'parameter-case')
	def parameter_record(self, resolver, items, attr):
		"""
		# Format the (id)`parameter-case` element substituted by &join_synopsis_details.
		"""
		arglist = attr['arguments']
		argtext = (self.text(a.sole.data) for a in arglist)
		*args, _ = tools.interlace(argtext, itertools.repeat(' , '))
		yield self.element('.It', 'Fa', *args)

	@comethod('directory')
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

	@comethod('paragraph')
	def normal_paragraph(self, resolver, elements, attr):
		if attr.get('index', -1) != 0:
			# Ignore initial paragraphs breaks in sequences.
			yield self.element('.Pp')
		yield from self.paragraph(resolver, elements, attr)

	def paragraph(self, resolver, pnodes, attr, *, interpret=iparagraph):
		for qual, txt in interpret(pnodes):
			typ, subtype, *local = qual.split('/')

			# Filter void zones.
			if len(local) == 1 and local[0] == 'void':
				continue

			yield resolver(typ, subtype)(resolver, attr, txt, *local)

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
			macro = literal_casts.get(cast, '.Ql')
			return self.element(macro, self.text(text), 'Ns')

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
		p = structure_paragraph_element(i[1][0])
		yield p #* Not a sole reference.

def recognize_synopsis_options(section):
	e = None
	for si, e in enumerate(section):
		if e[0] in {'directory'}:
			del section[si:si+1]
			break
	else:
		return []

	return [
		(i[-1]['identifier'],
			structure_paragraph_element(i[1][0]).sole.type.split('/')[-1],
			list(map(split_option_flags, _pararefs(i)))
		)
		for i in e[1]
	]

def join_synopsis_details(context, index, synsect='SYNOPSIS'):
	"""
	# Join some of the information defined in `OPTIONS` or `PARAMETERS`
	# with the references cited in `SYNOPSIS`.
	"""
	if ('OPTIONS',) in index:
		relation = 'OPTIONS'
		case_id = 'option-case'
	elif ('PARAMETERS',) in index:
		relation = 'PARAMETERS'
		case_id = 'parameter-case'
	else:
		relation = ''

	fields = {}
	# Get ordered list of names.
	names = []
	types = []
	# Parameter list for each name.
	optlists = collections.defaultdict(list)
	# The option set for each option reference.
	optindex = {}

	if (synsect,) in index:
		syn, _ = index[(synsect,)] #* No SYNOPSIS?
		synopts = recognize_synopsis_options(syn[1])
	else:
		syn = None
		synopts = ()

	for subjname, typ, options in synopts:
		names.append(subjname)
		types.append(typ)
		optlists[subjname].extend(options)
		for optref, optset in options:
			optindex[optref] = optset

	if not names:
		names = [p.sole.data for p in context.get('names', ())]

	if ('NAME',) in index:
		index[('NAME',)][0][-1]['names'] = names

	if (relation,) not in index:
		return relation

	xrs, _ = index[(relation,)] #* Missing OPTIONS/PARAMETERS?
	for element in xrs[1]:
		if element[0] not in {'directory'}:
			continue

		# First directory, structure synopsis.
		for i in element[1]:
			# Name and Parameter/Option list.
			arglist = []
			key, value = i[1]

			refname = i[-1]['identifier']
			first = value[1][0]

			if first[0] == 'sequence':
				arglist = [structure_paragraph_element(x[1][0]) for x in first[1]]
				del value[1][:1]

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
		# No directory in found section.
		raise Exception("synopsis option section contained no directory")

	if syn is not None:
		sa = syn[-1]
		sa['names'] = names
		sa['types'] = types
		sa['options'] = optlists
		sa['fields'] = fields

	return relation

def transform(prefix, chapter, identifier='', type=''):
	idx = chapter[-1]['index']
	ctx = chapter[-1]['context']
	rel = join_synopsis_details(ctx, idx)
	man = Render(None, ctx, prefix, idx, navigate(chapter), rel.lower())
	return man.document(type, identifier)
