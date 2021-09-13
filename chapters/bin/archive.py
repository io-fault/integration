"""
# Construct an archive for a Product's Internet Representation.

# This provides the input used by &.daemon web partitions.
"""
import os
import traceback
import zipfile
import contextlib
import json

from fault.context import tools
from fault.context.types import Cell
from fault.system import files
from fault.system import execution
from fault.system import process
from fault.project import system as lsf

from .. import join

def apath(*parts):
	return '/'.join(parts)

@tools.cachedcalls(8)
def mkvariants(intention, system, architecture):
	return lsf.types.Variants(
		system=system,
		architecture=architecture,
		intention=intention,
		form='delineated',
	)

def r_factor(variants, archive, req, ctx, pj, pjdir, fpath, type, requirements, sources):
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
	meta_json = json.dumps([meta_prefix, primary, str(type)]).encode('utf-8')
	archive.writestr(meta, meta_json)

	for v in variants:
		img = pj.image(v, fpath)
		if img.fs_type() == 'directory':
			break
	else:
		# No image.
		return ""

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

def r_project(variants, archive, req:lsf.Context, ctx:lsf.Context, pj:lsf.Project):
	# Currently hardcoded.
	pjdir = str(pj.factor)
	factors = []

	for ((path, type), (reqs, sources)) in pj.select(lsf.types.factor):
		summary = r_factor(variants, archive, req, ctx, pj, pjdir, path, type, reqs, sources)
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
	outstr, ctxpath, *variant_s = inv.argv

	# Build project context for the target product.
	ctx = lsf.Context()
	pd = ctx.connect(files.Path.from_absolute(ctxpath))
	ctx.load()
	ctx.configure()

	# Construct dependency context.
	req = ctx.from_product_connections(pd)
	req.load()

	variants = [
		mkvariants('coverage', x[0], x[1]) for x in (
			y.split('/') for y in variant_s
		)
	]

	out = files.Path.from_path(outstr)
	arc = zipfile.ZipFile(str(out), mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9)
	with arc:
		projects = []
		for pj in ctx.iterprojects():
			r_project(variants, arc, req, ctx, pj)
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
