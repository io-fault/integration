"""
# Print representations of factors for publication and reading.
"""
import sys
import os
import traceback
import contextlib
import json
import collections

from fault.vector import recognition
from fault.context import tools
from fault.context.types import Cell
from fault.system import files
from fault.system import process
from fault.project import system as lsf

from fault.text.io import structure_chapter_text, structure_paragraph_element
from . import join
from . import html
from ..metrics import coverage

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
	fmeta = froot + ['meta.json']
	fcoverage = froot + ['coverage.json']
	fmetrics = froot + ['metrics.json']

	# Identify whether the factor is a sole source and what that source (file) is.
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
			break
	else:
		img = files.root/'var'/'empty'/'nothing'

	for v in variants:
		metrics = pj.image(v.reform('metrics'), fpath)
		if metrics.fs_type() == 'directory':
			try:
				careas, ccounts, ctypes = coverage.load_metrics_aggregates(metrics)
			except FileNotFoundError:
				continue
			else:
				break
	else:
		metrics = files.root/'var'/'empty'/'nothing'
		careas = {}
		ccounts = {}
		ctypes = {}

	srcindex = []
	chapter = ""
	ctxcov = {}
	cc = 0 # Total positive counters.
	cz = 0 # Total zero counters.

	# Populate source tree with delineation and metrics.
	for fmt, x in sources:
		# Per-source, implied, per-element dictionary used by join.
		annotations = collections.defaultdict(dict)

		# Calculate path to delineation image.
		if str(fmt) == 'http://if.fault.io/factors/meta.unknown':
			# Ignore unknown sources.
			continue

		rpath = x.points
		rpathstr = '/'.join(rpath)
		outsrc = fsrc + list(rpath)
		depth = len(rpath) + ddepth

		fmt = fmt.format
		srcindex.append((rpathstr, fmt.language, fmt.dialect))

		# Coverage Data
		apath = str(x)
		areas = careas.pop(apath, {})
		types = ctypes.pop(apath, "")
		counts = ccounts.pop(apath, {})
		src_cc = 0
		src_cz = 0

		# Factor Images
		di = img + rpath

		# project/factor/src/path.ext/source.txt
		yield outsrc + ['source.txt'], (x.fs_load(),)

		if di.fs_type() == 'directory':
			# Emit coverage profile for the factor's source.
			try:
				with (di/'elements.json').fs_open('r') as f:
					elements_data = json.load(f)
			except:
				cidx = {}
				covp = None
				raise
			else:
				covp = coverage.factor_source_profile(elements_data, areas, types, counts)
				covzeros = set(covp['zeros'])
				for eid, eareas in covp['elements'].items():
					c = ctxcov[eid] = coverage.annotation(covzeros, eareas)
					annotations[eid]['coverage'] = c
					cc += c[0]
					src_cc += c[0]
					cz += c[1]
					src_cz += c[1]
				# Identify file with relative path.
				ctxcov['/'+rpathstr] = ctxcov.pop('', [])
				# Per-source totals.
				annotations['']['coverage'] = [src_cc, src_cz]

				# Per-element counters.
				yield outsrc + ['metrics', 'coverage.json'], (json.dumps(covp).encode('utf-8'),)

			if (di/'context.json').fs_type() == 'data':
				# If context extraction was performed, merge with meta.json.
				with (di/'context.json').fs_open() as f:
					meta_json.update(json.load(f))

			# Copy the contents of the delineation image.
			for dirpath, dfiles in di.fs_index():
				for f in dfiles:
					yield outsrc + ['delineated', f.identifier], (f.fs_load(),)

			rr = join.Resolution(req, ctx, pj, fpath)
			fet = ''.join(join.transform(annotations, rr, di, x))
			yield outsrc + ['chapter.txt'], (fet.encode('utf-8'),)

			chapter += "\n[]\n"
			chapter += fet

	# Has a metrics image?
	if metrics.fs_type() == 'directory':
		# Copy the contents of the metrics image.
		syntax_metrics = json.loads((metrics/'syntax-profiles').fs_load())
		line_count = 0
		for syntax_file in syntax_metrics.values():
			for sr in syntax_file:
				line_count += sr['count']
	else:
		syntax_metrics = None
		line_count = None

	metrics_summary = {
		'coverage': (cc - cz) / cc if cc > 0 else None,
		'traversable': cc, # Total number of coverage counters.
		'revealed': cz, # Total number of coverage counters that were zero.
		'line-count': line_count,
		'syntax': syntax_metrics,
	}

	yield fcoverage, (json.dumps(ctxcov).encode('utf-8'),)
	yield fmetrics, (json.dumps(metrics_summary).encode('utf-8'),)
	yield fmeta, (json.dumps(meta_json).encode('utf-8'),)
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
	depth = 2 # Corpus / Project / [Factor]
	ident = str(pj.factor//fpath)
	sub = html.PageSubject(
		html.factor_type_icon(depth, str(type)), fpath.identifier,
		str(type.factor), str(type)
	)
	ctx = html.PageContext(pj.extensions.icon, str(pj.factor), '../')

	head = html.r_head(sx, sx.xml_encoding, styles(depth, factor_style), title=ident)
	yield froot + ['index.html'], html.r_factor_page(sx, prefix, depth, sub, ctx, chapter, head=head)

	# Render source index, but not src/index.html as it may conflict with an actual source.
	yield froot + ['src', '.http-resource', 'index.json'], (json.dumps(srcindex).encode('utf-8'),)

	depth += 1 # Corpus / Project / Factor / [Source]
	sihead = html.r_head(sx, sx.xml_encoding, styles(depth, sources_style), title=ident)
	srctyp = 'http://if.fault.io/factors/meta.sources'
	icon = html.factor_type_icon(depth, srctyp)
	srcsub = html.PageSubject(icon, '/src/', 'meta.sources', srctyp)
	srcctx = html.PageContext(pj.extensions.icon, ident, '../')

	index = html.r_sources(sx, srcindex)
	sihtml = list(html.indexframe(sx, sihead, srcsub, srcctx, index, depth=depth))
	yield froot + ['src', '.http-resource', 'index.html'], sihtml
	yield froot + ['src', 'index.html'], sihtml

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

	typ = 'http://if.fault.io/factors/meta.project'
	ctxtyp = 'http://if.fault.io/factors/meta.corpus'
	icon = pj.extensions.icon or html.factor_type_icon(1, typ)
	sub = html.PageSubject(icon, pj.factor.identifier, 'meta.project', typ)
	ctx = html.PageContext(html.factor_type_icon(1, ctxtyp), str(pj.factor ** 1), '../')

	yield [pjdir, 'index.html'], html.indexframe(sx, head, sub, ctx, html.r_factors(sx, index), depth=1)

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

	sub = html.PageSubject(html.factor_type_icon(0, ctype), title, 'meta.corpus', ctype)
	ctx = html.PageContext('//favicon.ico', '', '/')
	index = html.r_projects(sx, projects)
	yield ['index.html'], html.indexframe(sx, head, sub, ctx, index)

	if config['web-defaults']:
		default = (files.Path.from_absolute(__file__) ** 1)/'theme'

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
		local = out@('.factor-type-icon/' + html.icon_identity(str(ft)) + '.svg')
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

def manual(argv, variants=lsf.types.Variants('void', 'json', 'delineated')):
	"""
	# Print system manuals from chapter elements.
	"""

	from .manual import transform, prepare

	job = argv[0]
	if job == 'page':
		src = process.fs_pwd() @ argv[1]
		chapter = prepare(structure_chapter_text(src.fs_load().decode('utf-8')))
		sys.stdout.writelines(
			x + '\n'
			for x in transform('', chapter)
		)
		return
	elif job != 'factors':
		sys.stderr.write(f"ERROR: unknown job {job!r}; only 'page'.\n")
		return 1

	marg_restrict = {}
	marg_require = {}
	config = {
		'encoding': 'utf-8',
		'prefixes': set(),
	}
	v = recognition.legacy(marg_restrict, marg_require, argv[1:])
	remainder = recognition.merge(config, v)
	out, productpath = map(process.fs_pwd().__matmul__, remainder[:2])
	projects = remainder[2:]
	outenc = config['encoding']

	# Build factor context for the target product.
	factors = lsf.Context()
	products = list(map(factors.connect, [productpath]))
	factors.load()
	factors.configure()
	requirements = list(map(factors.from_product_connections, products))

	# Filter to selected projects.
	if projects:
		projects = set(projects)
		iprojects = (
			x for x in factors.iterprojects()
			if str(x.factor) in projects
		)
	else:
		iprojects = factors.iterprojects()

	# Print manual factors available in the factor context.
	for pj in iprojects:
		for fi, fd in pj.select(lsf.types.factor):
			fp, ft = fi
			if str(ft) != 'http://if.fault.io/factors/meta.chapter':
				# Filter non-chapter factors.
				continue

			# Get factor image.
			fmt, file = fd[1][0]
			i = pj.image(variants, fp) / file.identifier

			ctx = json.loads((i / 'context.json').fs_load().decode('utf-8'))
			if ctx['protocol'] != 'http://if.fault.io/chapters/system.manual':
				# Filter non-manual texts.
				continue

			chapter_path = (i / 'elements.json')
			chapter_json = chapter_path.fs_load().decode('utf-8')

			chapter = prepare(json.loads(chapter_json)[1][0])
			mansection = str(chapter[-1]['context']['section'].sole[1])
			manpath = out/('man' + mansection)
			manpath = manpath/(fp.identifier + '.' + mansection)

			with manpath.fs_alloc().fs_open('w', encoding=outenc) as f:
				f.writelines(
					x + '\n'
					for x in transform('', chapter)
				)

def web(argv):
	"""
	# Print factor representations for web publication.
	"""

	job = argv[0]
	if job == 'page':
		src = process.fs_pwd() @ argv[1]
		styles = [process.fs_pwd() @ x for x in argv[2:]]
		sys.stdout.buffer.writelines(html.r_page(src, styles))
		return

	config = {
		'encoding': 'utf-8',
		'corpus-root': '',
		'corpus-title': 'corpus',
		'prefixes': set(),
		'web-defaults': True,
	}
	v = recognition.legacy(restricted, required, argv[1:])
	remainder = recognition.merge(config, v)
	out, ctxpath = map(process.fs_pwd().__matmul__, remainder)

	# Build project context for the target product.
	factors = lsf.Context()
	pd = factors.connect(ctxpath)
	factors.load()
	factors.configure()

	# Construct dependency context.
	req = factors.from_product_connections(pd)
	req.load()

	# Identify variants to scan for delineated sources.
	variants = [
		lsf.types.Variants(*x.identifier.split('-'), form='delineated')
		for x in (ctxpath/'.delineated').fs_list()[0]
	]

	out.fs_mkdir()
	if job == 'icons':
		icons(out, factors, set([
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
	elif job == 'factors':
		for rpath, data in r_corpus(config, out, factors, req, variants):
			path = out + rpath
			try:
				with path.fs_alloc().fs_open('wb') as f:
					f.writelines(data)
			except:
				print('->', str(path), file=sys.stderr)
				traceback.print_exc()
				import pdb
				pdb.set_trace()
	else:
		sys.stderr.write(f"ERROR: unknown job {job!r}; only 'factors', 'icons', 'page'.\n")
		return 1

def main(inv:process.Invocation) -> process.Exit:
	ptype = inv.argv[0]

	try:
		if ptype == 'web':
			code = web(inv.argv[1:])
		elif ptype == 'manual':
			code = manual(inv.argv[1:])
		else:
			sys.stderr.write("ERROR: only 'web' and 'manual' types are supported.\n")
			code = 1
	except Exception as err:
		import pdb, traceback
		traceback.print_exc()
		pdb.post_mortem(err.__traceback__)
		code = 1

	return inv.exit(code or 0)
