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

from .. import join
from .. import html

web_resources = ".legacy-web"
core_style = "core.css"

project_index_style = "corpus.css"
factor_index_style = "project.css"
factor_style = "factor.css"
chapter_style = "chapter.css"

def styles(depth, type, directory=web_resources):
	prefix = '../' * depth
	return [
		prefix + directory + '/' + core_style,
		prefix + directory + '/' + type,
	]

def abstract(project):
	for factor in project.select(lsf.types.factor@'documentation'):
		(fp, ft), (fr, fs) = factor
		if fp.identifier != 'project':
			continue
		(fmt, src), = fs
		break

	cursor = html.nodes.Cursor.from_chapter_text(src.get_text_content())
	try:
		ipara, = cursor.select("/dictionary/item[icon]/value/paragraph#1")
		icon = html.nodes.document.export(ipara[1]).sole.data
	except:
		traceback.print_exc()
		icon = None

	first, = cursor.select("/section[Abstract]/paragraph#1")
	para = html.nodes.document.export(first[1])
	for s in para.sentences:
		return icon, ''.join(x[1] for x in s)
	else:
		return icon, ''

def r_factor(sx, prefixes, variants, req, ctx, pj, pjdir, fpath, type, requirements, sources):
	# project/factor
	img = None
	metrics = None

	froot = [pjdir, str(fpath)]
	fsrc = froot + ['src']

	meta = froot + ['meta.json']
	if isinstance(sources, Cell):
		meta_prefix = False
		primary = sources[0][1].identifier
		ddepth = 0
	else:
		ddepth = 1
		meta_prefix = True
		primary = ""
	meta_json = json.dumps([meta_prefix, primary, str(type)])
	yield meta, (meta_json.encode('utf-8'),)

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
			# Copy the contents of the delineation image.
			for dirpath, dfiles in di.fs_index():
				for f in dfiles:
					yield outsrc + ['delineated', f.identifier], (f.fs_load(),)

			rr = join.Resolution(req, ctx, pj, fpath)
			fet = ''.join(join.transform(rr, di, x))
			yield outsrc + ['chapter.txt'], (fet.encode('utf-8'),)

			chapter += "\n[]\n"
			chapter += fet

	for x in prefixes:
		if str(pj.factor).startswith(x):
			prefix = x
			break
	else:
		prefix = ''

	ident = str(pj.factor//fpath)
	head = html.r_head(sx, sx.xml_encoding, styles(2, factor_style), title=ident)
	ht = html.transform(sx, prefix, ddepth+2, chapter, head=head, identifier=ident, type=str(type))

	yield froot + ['index.html'], ht
	yield froot + ['src.json'], (json.dumps(srcindex).encode('utf-8'),)

def r_project(sx, prefixes, variants, req:lsf.Context, ctx:lsf.Context, pj:lsf.Project, pjdir):
	# Currently hardcoded.
	index = []

	for ((fp, ft), (fr, fs)) in pj.select(lsf.types.factor):
		if str(ft) == 'http://if.fault.io/factors/meta.unknown':
			# Ignore unknown factors.
			continue

		yield from r_factor(sx, prefixes, variants, req, ctx, pj, pjdir, fp, ft, fr, fs)
		index.append((str(fp), str(ft), list(map(str, fr))))

	yield [pjdir, '.index.json'], (json.dumps(index).encode('utf-8'),)

	head = html.r_head(sx, sx.xml_encoding,
		styles(1, factor_index_style),
		title=str(pj.factor)
	)
	yield [pjdir, 'index.html'], html.factorindex(sx, head, str(pj.factor), index)

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
	sx = html.xml.Serialization(xml_encoding=config['encoding'])

	outstr, ctxpath, *variant_s = remainder

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

	projects = []
	for pj in ctx.iterprojects():
		try:
			icon, projectabstract = abstract(pj)
		except:
			icon = ''
			projectabstract = ''
		pjdir = removeprefix(config['prefixes'], str(pj.factor))

		for rpath, rcontent in r_project(sx, config['prefixes'], variants, req, ctx, pj, pjdir):
			apath = out + rpath
			with apath.fs_alloc().fs_open('wb') as f:
				try:
					f.writelines(rcontent)
				except:
					#print(str(apath), file=sys.stderr)
					traceback.print_exc()

		projects.append((
			removeprefix(config['prefixes'], str(pj.factor)),
			str(pj.factor),
			str(pj.identifier),
			icon,
			str(pj.protocol.identifier),
			projectabstract,
		))

	with (out/'.index.json').fs_open('w') as f:
		f.write(json.dumps(projects, ensure_ascii=False))
	head = html.r_head(sx,
		config['encoding'],
		styles(0, project_index_style),
		title=config['corpus-title'],
	)
	with (out/'index.html').fs_open('wb') as f:
		if config['corpus-root']:
			# User declared corpus representation.
			ctype = 'http://if.fault.io/factors/meta.corpus'
		else:
			ctype = 'http://if.fault.io/factors/meta.product'
		title = config['corpus-title']
		croot = config['corpus-root']
		f.writelines(html.projectindex(sx, head, croot, title, projects, type=ctype))

	if config['web-defaults']:
		wr = (out/web_resources)
		t = wr/'default'
		default = (files.Path.from_absolute(__file__) ** 2)/'theme'

		# Copy all of theme to .legacy-web/default.
		t.fs_alloc().fs_mkdir().fs_replace(default)
		core = (wr/'core.css')
		with core.fs_open('w') as f:
			f.writelines([
				"@import 'default/if.css';\n",
				"@import 'default/color.css';\n",
				"@import 'default/dark.css';\n",
				"@import 'default/admonition.css';\n",
				"@import 'default/index.css';\n",
				"@import 'default/log.css';\n",
			])

	return inv.exit(0)
