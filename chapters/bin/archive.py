"""
# Construct an archive for a Product's Internet Representation.

# This provides the input used by &.daemon web partitions.
"""
import os
import traceback
import zipfile
import contextlib
import json

from fault.context.types import Cell
from fault.project.root import Product, Context, Project
from fault.project import types as project_types
from fault.system import files
from fault.system import execution
from fault.system import process

from .. import join

def apath(*parts):
	return '/'.join(parts)

def r_factor(archive, req, ctx, pj, pjdir, fpath, type, requirements, sources):
	# project/factor
	outset = apath(pjdir, str(fpath))

	meta = apath(outset, '.meta.json')
	if isinstance(sources, Cell):
		meta_prefix = False
		primary = sources[0][1].identifier
		ddepth = 0
	else:
		ddepth = 1
		meta_prefix = True
		primary = ""
	meta_json = json.dumps([meta_prefix, primary, type]).encode('utf-8')
	archive.writestr(meta, meta_json)

	vars = {
		'intention': 'delineation',
		'architecture': 'data',
		'system': 'void',
	}

	img = pj.image(vars, fpath)
	srcindex = []
	for x in (x[1] for x in sources):
		# Calculate path to delineation image.
		rpath = x.points
		depth = (len(rpath) - 1) + ddepth
		srcindex.append(x.points)
		srcdir = img + rpath
		outsrc = apath(outset, *rpath)

		if srcdir.fs_type() == 'directory':
			# Copy the contents of the delineation image.
			for dirpath, files in srcdir.fs_index():
				for f in files:
					path = f.segment(srcdir)
					archive.write(str(f), apath(outsrc, *path))

			outtxt = apath(outsrc, '.chapter.txt')
			try:
				rr = join.Resolution(req, ctx, pj, fpath)
				archive.writestr(outtxt, ''.join(join.transform(rr, srcdir, x)))
			except Exception:
				traceback.print_exc()

		srctxt = apath(outsrc, 'source.txt')
		archive.write(str(x), srctxt)

	archive.writestr(apath(outset, '.index.json'), json.dumps(srcindex))
	return ""

def r_project(archive, req:Context, ctx:Context, pj:Project):
	# Currently hardcoded.
	pj.protocol.parameters.update({
		'source-extension-map': {
			'py': ('python-module', set()),
			'txt': ('chapter', set()),
		}
	})
	pjdir = str(pj.factor)
	factors = []

	for ((path, type), (reqs, sources)) in pj.select(project_types.factor):
		summary = r_factor(archive, req, ctx, pj, pjdir, path, type, reqs, sources)
		factors.append((str(path), str(type), summary))

	archive.writestr(apath(pjdir, '.index.json'), json.dumps(factors))

def archive(output, input):
	import os.path
	zf = zipfile.ZipFile(str(output), mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)
	with zf:
		istr = str(input)
		prefix = istr + '/'
		plen = len(prefix)

		for root, dirs, files in os.walk(istr):
			for file in files:
				ipath = os.path.join(root, file)
				zf.write(ipath, arcname=ipath[plen:])

def first_sentence(p):
	for x in p.sentences:
		if not x:
			continue

		return ''.join(y[1] for y in x)

	# None detected, presume single sentence abstract.
	return ''.join(y[1] for y in p)

def main(inv:process.Invocation) -> process.Exit:
	outstr, ctxpath = inv.argv

	# Build project context for the target product.
	ctx = Context()
	pd = ctx.connect(files.Path.from_absolute(ctxpath))
	ctx.load()

	# Construct dependency context.
	req = ctx.from_product_connections(pd)
	req.load()

	out = files.Path.from_path(outstr)
	arc = zipfile.ZipFile(str(out), mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)
	with arc:
		projects = []
		for pj in ctx.iterprojects():
			r_project(arc, req, ctx, pj)
			projects.append(pj)

		pjidx = [
			(
				str(pj.factor),
				str(pj.identifier),
				pj.information.icon,
				str(pj.protocol.identifier),
				first_sentence(pj.information.abstract)
			)
			for pj in projects
		]
		arc.writestr('.index.json', json.dumps(pjidx, ensure_ascii=False))

	return inv.exit(0)
