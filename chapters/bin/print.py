"""
# Construct an archive for a Product's Internet Representation.

# This provides the input used by &.daemon web partitions.
"""
import sys
import os
import traceback
import contextlib
import json

from fault.vector import recognition
from fault.context import tools
from fault.context.types import Cell
from fault.system import files
from fault.system import process
from fault.project import system as lsf

from fault.text.io import structure_chapter_text, structure_paragraph_element
from .. import join
from .. import html

web_resources = '.legacy-web'
core_style = 'core.css'

project_index_style = 'corpus.css'
factor_index_style = 'project.css'
factor_style = 'factor.css'
chapter_style = 'chapter.css'
sources_style = 'sources.css'

def styles(depth, type, directory=web_resources):
	prefix = '../' * depth
	return [
		prefix + directory + '/' + core_style,
		prefix + directory + '/' + type,
	]

def r_factor(sx, prefixes, variants, req, ctx, pj, pjdir, fpath, type, requirements, sources):
	# project/factor
	img = None
	metrics = None

	froot = [pjdir, str(fpath)]
	fsrc = froot + ['src']

	meta = froot + ['.http-resource', 'meta.json']
	if isinstance(sources, Cell):
		sole = True
		primary = sources[0][1].identifier
		ddepth = 0
	else:
		ddepth = 1
		sole = False
		primary = ""

	meta_json = {
		'sole': primary,
		'level': ddepth,
		'type': str(type),
		'identifier': str(fpath),
	}

	for v in variants:
		img = pj.image(v.reform('delineated'), fpath)
		if img.fs_type() == 'directory':
			metrics = pj.image(v.reform('metrics'), fpath)
			break
	else:
		img = files.root/'var'/'empty'/'nothing'
		metrics = files.root/'var'/'empty'/'nothing'

	srcindex = []
	chapter = ""

	# Populate source tree with delineation and metrics.
	for fmt, x in sources:
		# Calculate path to delineation image.
		if str(fmt) == 'http://if.fault.io/factors/meta.unknown':
			# Ignore unknown sources.
			continue

		rpath = x.points
		outsrc = fsrc + list(rpath)
		depth = len(rpath) + ddepth

		fmt = fmt.format
		srcindex.append(('/'.join(x.points), fmt.language, fmt.dialect))

		# Factor Images
		di = img + rpath
		mi = metrics + rpath

		# project/factor/src/path.ext/source.txt
		yield outsrc + ['source.txt'], (x.fs_load(),)

		if mi.fs_type() == 'directory':
			# Copy the contents of the metrics image.
			for dirpath, mfiles in mi.fs_index():
				for f in mfiles:
					yield outsrc + ['metrics', f.identifier], (f.fs_load(),)

		if di.fs_type() == 'directory':
			if (di/'context.json').fs_type() == 'data':
				# If context extraction was performed, merge with meta.json.
				with (di/'context.json').fs_open() as f:
					meta_json.update(json.load(f))

			# Copy the contents of the delineation image.
			for dirpath, dfiles in di.fs_index():
				for f in dfiles:
					yield outsrc + ['delineated', f.identifier], (f.fs_load(),)

			rr = join.Resolution(req, ctx, pj, fpath)
			fet = ''.join(join.transform(rr, di, x))
			yield outsrc + ['chapter.txt'], (fet.encode('utf-8'),)

			chapter += "\n[]\n"
			chapter += fet

	yield meta, (json.dumps(meta_json).encode('utf-8'),)
	if 'icon' in meta_json:
		icon_data = meta_json['icon']
		if 'image/svg' in icon_data:
			try:
				empty, b64 = icon_data.split('data:image/svg+xml;base64,', 1)
			except ValueError:
				pass
			else:
				import base64
				svg = base64.b64decode(b64)
				yield (froot + ['.http-resource', 'icon.svg'], (svg,))

	for x in prefixes:
		if str(pj.factor).startswith(x):
			prefix = x
			break
	else:
		prefix = ''

	# Factor Representation Resource
	ident = str(pj.factor//fpath)
	head = html.r_head(sx, sx.xml_encoding, styles(2, factor_style), title=ident)
	ht = html.transform(sx, prefix, ddepth+2, chapter, head=head, identifier=ident, type=str(type))
	yield froot + ['index.html'], ht

	# Render source index, but not src/index.html as it may conflict with an actual source.
	yield froot + ['src', '.http-resource', 'index.json'], (json.dumps(srcindex).encode('utf-8'),)
	sihead = html.r_head(sx, sx.xml_encoding, styles(3, sources_style), title=ident)
	sihtml = html.sourceindex(sx, sihead, ident, srcindex)
	yield froot + ['src', '.http-resource', 'index.html'], sihtml

def r_project(sx, prefixes, variants, req:lsf.Context, ctx:lsf.Context, pj:lsf.Project, pjdir):
	# Currently hardcoded.
	index = []

	for ((fp, ft), (fr, fs)) in pj.select(lsf.types.factor):
		if str(ft) == 'http://if.fault.io/factors/meta.unknown':
			# Ignore unknown factors.
			continue

		yield from r_factor(sx, prefixes, variants, req, ctx, pj, pjdir, fp, ft, fr, fs)
		index.append((str(fp), str(ft), list(map(str, fr))))

	yield [pjdir, '.http-resource', 'index.json'], (json.dumps(index).encode('utf-8'),)

	head = html.r_head(sx, sx.xml_encoding,
		styles(1, factor_index_style),
		title=str(pj.factor)
	)
	yield [pjdir, 'index.html'], html.factorindex(sx, head, str(pj.factor), index)

def hrinit(prefix, type, identifier, resource='index', meta={}):
	"""
	# Initialize the `.http-resource` directory inside &path
	# with a `meta.json` formed from &meta, &type, and &identifier.

	# Returns the directory path that was created.
	"""

	m = dict(meta)
	m['type'] = type
	m['identifier'] = identifier
	m['resource'] = resource

	path = prefix + ['.http-resource', 'meta.json']
	idata = (json.dumps(m, ensure_ascii=False).encode('utf-8'),)
	return path, idata

def r_corpus(config, out, ctx, req, variants):
	sx = html.xml.Serialization(xml_encoding=config['encoding'])

	projects = []
	for pj in ctx.iterprojects():
		ext = pj.extensions
		pjdir = removeprefix(config['prefixes'], str(pj.factor))
		yield hrinit([pjdir], 'http://if.fault.io/factors/meta.project', str(pj.factor))
		yield from r_project(sx, config['prefixes'], variants, req, ctx, pj, pjdir)

		projects.append((
			removeprefix(config['prefixes'], str(pj.factor)),
			str(pj.factor),
			str(pj.identifier),
			ext.icon,
			str(pj.protocol.identifier),
			ext.synopsis,
		))

	# Either an anonymous product or an identified corpus.
	title = config['corpus-title']
	ctype = ''
	if config['corpus-root']:
		ctype = 'http://if.fault.io/factors/meta.corpus'
		croot = config['corpus-root']
	else:
		ctype = 'http://if.fault.io/factors/meta.product'
		croot = str(out)

	yield hrinit([], ctype, croot)
	yield ['.http-resource', 'index.json'], (json.dumps(projects, ensure_ascii=False).encode('utf-8'),)

	head = html.r_head(sx,
		config['encoding'],
		styles(0, project_index_style),
		title=config['corpus-title'],
	)

	yield ['index.html'], html.projectindex(sx, head, ctype, croot, title, projects)

	if config['web-defaults']:
		default = (files.Path.from_absolute(__file__) ** 2)/'theme'

		# Copy all of theme to .legacy-web/default.
		for f in default.fs_iterfiles(type='data'):
			if f.identifier.startswith('.'):
				continue
			yield [web_resources, 'default', f.identifier], (f.fs_load(),)

		yield [web_resources, 'core.css'], (''.join([
			"@import 'default/context.css';\n",
			"@import 'default/sheet.css';\n",
			"@import 'default/if.css';\n",
			"@import 'default/select.css';\n",
			"@import 'default/icon.css';\n",
			"@import 'default/admonition.css';\n",
			"@import 'default/index.css';\n",
			"@import 'default/log.css';\n",
		]).encode('utf-8'),)

def first_sentence(p):
	for x in p.sentences:
		if not x:
			continue

		return ''.join(y[1] for y in x)

	# None detected, presume single sentence abstract.
	return ''.join(y[1] for y in p)

def removeprefix(prefixes, string):
	for prefix in prefixes:
		if string.startswith(prefix):
			return string[len(prefix):]
	return string

required = {
	'--corpus-root': ('field-replace', 'corpus-root'),
	'--corpus-title': ('field-replace', 'corpus-title'),
	'-P': ('set-add', 'prefixes'),
}

restricted = {
	'-W': ('field-replace', False, 'web-defaults'),
	'-w': ('field-replace', True, 'web-defaults'),
}

def extract_image_reference(svg):
	"""
	# Extract the hyperlink from the first image element in an SVG image.
	# The `href` attribute must be directly adjacent to the `=` character.

	# [ Parameters ]
	# /svg/
		# The SVG XML string.
	# [ Returns ]
	# /&str/
		# The contents of the href attribute.
	# [ Exceptions ]
	# /&ValueError/
		# No image tag with an href attribute.
	"""
	imgat = svg.find('<image')
	prefix, href = svg[imgat+6:].split('href=', 1)
	return href[1:href.find(href[:1], 1)]

def transfer(xfers):
	"""
	# Transfer the remote resources to their associated filesystem location.
	"""
	from system.root import query
	from fault.system import execution
	fd = str(query.libexec() / 'fault-dispatch')

	for remote, local in xfers:
		ki = execution.KInvocation(fd, [fd, 'http-cache', str(remote), str(local)])
		execution.perform(ki)

def icons(out:files.Path, ctx:lsf.Context, types):
	"""
	# Print the icons of the factor types used by the projects in &ctx.
	# The icons are placed stored in `.factor-type-icon/` relative to &out
	# according to &html.icon_identity.
	"""
	for pj in ctx.iterprojects():
		for ((fp, ft), (fr, fs)) in pj.select(lsf.types.factor):
			types.add(ft)

	xfer_index = []
	for ft in types:
		remote = str(ft) + '/.http-resource/icon.svg'
		local = out@(html.icon_identity(str(ft)) + '.svg')
		local.fs_alloc()
		if local.fs_type() == 'data':
			local.fs_void()
		xfer_index.append((remote, local))

	# Transfer resources to the local filesystem.
	transfer(xfer_index)

	# Check for nested images. Presume SVG.
	overwrites = []
	for r, f in xfer_index:
		try:
			ref = extract_image_reference(f.fs_load().decode('utf-8'))
			if not ref.startswith('data:'):
				overwrites.append((ref, f))
				f.fs_void()
		except ValueError:
			pass
	transfer(overwrites)

def main(inv:process.Invocation) -> process.Exit:
	config = {
		'encoding': 'utf-8',
		'corpus-root': '',
		'corpus-title': 'corpus',
		'prefixes': set(),
		'web-defaults': True,
	}
	v = recognition.legacy(restricted, required, inv.argv)
	remainder = recognition.merge(config, v)

	rformat, outstr, ctxpath, *variant_s = remainder
	if rformat not in {'web', 'icons'}:
		sys.stderr.write("ERROR: only 'web' and 'icons' format is supported.\n")
		return inv.exit(1)

	# Build project context for the target product.
	ctx = lsf.Context()
	pd = ctx.connect(files.Path.from_absolute(ctxpath))
	ctx.load()
	ctx.configure()

	# Construct dependency context.
	req = ctx.from_product_connections(pd)
	req.load()

	variants = [
		lsf.types.Variants(*x.split('/'))
		for x in variant_s
	]

	out = files.Path.from_path(outstr)
	out.fs_mkdir()
	if rformat == 'icons':
		icons(out, ctx, set([
			'http://if.fault.io/factors/meta.sources',
			'http://if.fault.io/factors/meta.references',

			'http://if.fault.io/factors/meta.void',
			'http://if.fault.io/factors/meta.unknown',
			'http://if.fault.io/factors/meta.parameter',
			'http://if.fault.io/factors/meta.directory',
			'http://if.fault.io/factors/meta.project',
			'http://if.fault.io/factors/meta.corpus',
			'http://if.fault.io/factors/meta.product',
			'http://if.fault.io/factors/meta.type',
		]))
	elif rformat == 'web':
		for rpath, data in r_corpus(config, out, ctx, req, variants):
			path = out + rpath
			try:
				with path.fs_alloc().fs_open('wb') as f:
					f.writelines(data)
			except:
				print('->', str(path), file=sys.stderr)
				traceback.print_exc()

	return inv.exit(0)
