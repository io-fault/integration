"""
# Extract the delineated structures of the entire package tree into a
# &..filesystem.library.Dictionary instance.

# For composite factors and Python modules, the cached data from a constructed build
# using the inspect intention provides the sources for the target.
"""

import sys
import itertools
import os.path
import lzma
import types
import importlib.machinery
import pickle
from copy import deepcopy

from ...development import xml as devxml
from ...development import library as libdev
from ...system import libfactor
from ...routes import library as libroutes
from ...xml import libfactor as xmlfactor
from ...filesystem import library as libfs
from ...xml import library as libxml
lxml = xmlfactor.lxml

def join_metrics(document, metrics, test, project, cname, key):
	elements = devxml.materialize_metrics(libxml.Serialization(), metrics, test, str(project), cname, key)

	dq = lxml.Query(document, {'f': 'http://fault.io/xml/fragments'})
	r = dq.first('/f:factor')
	if r is None:
		return
	r = r.first('f:module|f:chapter|f:document')
	if r is None:
		return

	r = r.element

	for x in elements:
		if x:
			sub = xmlfactor.etree.fromstring(b''.join(x))
			r.addprevious(sub)

def module_fragments(route):
	pass

def emit(fs, key, iterator):
	r = fs.route(key)
	r.init('file')

	with r.open('wb') as f:
		# the xml declaration prefix is not written.
		# this allows stylesheet processing instructions
		# to be interpolated without knowning the declaration size.
		f.writelines(iterator)

def copy(ctx, target, package, metrics):
	"""
	# Copy the extracted fragments from the given package into the &target.

	# For Composite Factors, things are slightly complicated. In order to trivialize
	# the XML rendering, the &..development.schemas.fragments.context element need not
	# be presented as &copy will provide it along with other factor metadata.
	"""

	docs = libfs.Dictionary.create(libfs.Hash(), os.path.realpath(target))
	pkg = libroutes.Import.from_fullname(package)
	pkgset = list(libdev.gather_simulations([pkg]))

	if metrics is not None and isinstance(metrics, str):
		metrics = libfs.Dictionary.open(metrics)

	# Extension modules being an effect of inductence, the documentation
	# must be extracted at structure time.
	pexset = [
		x for x in pkg.tree()[0]
		if x.absolute[-1] == 'extensions'
	]
	from ...python import xml as d_python
	for pex in pexset:
		# Get the list of extension modules
		xr = [
			libfactor.extension_access_name(str(x)) for x in pex.tree()[0]
			if '__factor_domain__' in x.module().__dict__
		]
		xr = [libroutes.Import.from_fullname(x) for x in xr]
		xr = [(x, d_python.Context(x), x.module()) for x in xr]
		for r, sc, mod in xr:
			mod.__factor_composite__ = False
			k = libfactor.canonical_name(r).encode('utf-8')
			emit(docs, k, sc.serialize(mod))

	for f in pkgset:
		package_modules = set([
			x.identifier for x in f.module.__factor_sources__
		])

		vars, mech = ctx.select(f.domain)
		refs = libdev.references(f.dependencies())

		f_sources = list(f.link(dict(vars), ctx, mech, refs, ()))
		if not f_sources:
			# XXX: Use an empty directory and continue.
			# Note the absence of data instead of skipping.
			continue
		(sp, (vl, key, loc)), = f_sources

		iformat = 'xml'
		index = loc['integral']
		xi = (index / 'out') / iformat

		srctree = f.module.__factor_sources__
		rproject = f.route.floor()
		if rproject:
			project = libfactor.canonical_name(rproject)
			in_tests = str(f.route) == str(project) + '.test'
		else:
			project = None
			in_tests = False

		for y in package_modules:
			y = index / y
			if y.identifier not in package_modules:
				# Filter entries that are not Python modules.
				# This also keeps the loop from processing a composite.
				continue

			filename = y.identifier
			module_name = filename[:-len(y.extension)-1]

			if module_name == '__init__':
				fullname = f.module.__name__
				module_name = fullname[fullname.rfind('.')+1:]
				ispkg = True
			else:
				fullname = f.module.__name__ + '.' + module_name
				ispkg = False

			try:
				rroute = libroutes.Import.from_fullname(fullname)
				croute = libfactor.canonical_name(rroute)
			except ImportError as exc:
				print('could not import ', str(rroute), str(exc))
				continue

			cname = str(croute)
			if ispkg and libfactor.composite(rroute):
				iscomposite = True
			else:
				iscomposite = False

			rkey = str(croute).encode('utf-8')
			print(str(y))
			rdoc = xmlfactor.readfile(str(y))
			rdq = lxml.Query(rdoc, {'f': 'http://fault.io/xml/fragments'})
			rroot = rdq.first('/f:factor')

			if iscomposite:
				ctx_element = rroot.first('f:context').element

				cf = libdev.Factor(None, rroute.module(), None)
				print('composite:', cf.module.__name__, cf.domain)
				vars, mech = ctx.select(cf.domain)
				refs = libdev.references(cf.dependencies())

				c_sources = list(cf.link(dict(vars), ctx, mech, refs, ()))
				if not c_sources:
					# XXX: Use an empty directory and continue.
					# Note the absence of data instead of skipping.
					continue
				(sp, (vl, key, loc)), = c_sources

				dirs, sources = loc['integral'].tree()
				iformat = 'xml'
				index = loc['integral']
				xi = (index / 'out') / iformat

				sources = libfactor.sources(rroute)
				prefix = str(sources)
				prefix_len = len(prefix)

				# A target module that has a collection of sources.
				# Identify the source tree and find the interface description.
				srctree = sources.tree()
				for z in srctree[1]:
					if z.identifier.startswith('.'):
						# Ignore dot files.
						continue

					lang = libdev.languages.get(z.extension)
					suffix = str(z)[prefix_len+1:]
					fkey = (cname + '/' + suffix)
					print(fkey)
					depth = fkey.count('/')

					xis = os.path.join(str(index), suffix)
					try:
						doc = xmlfactor.readfile(xis)

						# Update positioning information; delineation is not required
						# to provide this information.
						dq = lxml.Query(doc, {'f': 'http://fault.io/xml/fragments'})
						r = dq.first('/f:factor')
						p = [
							k for k,v in r.element.nsmap.items()
							if k and v == 'http://fault.io/xml/fragments'
						]
						r.element.nsmap[None] = 'http://fault.io/xml/fragments'
						for ns in p:
							del r.element.nsmap[ns]

						r.element.attrib['path'] = suffix
						r.element.attrib['depth'] = ('../' * depth)
						r.element.attrib['name'] = cf.module.__name__
						r.element.attrib['identifier'] = module_name
						if in_tests:
							r.element.attrib['type'] = 'tests'

						# Inherit the context element from __init__.
						lctx = deepcopy(ctx_element)
						emod = r.first('f:module|f:document|f:chapter')
						emod = emod.element
						emod.addprevious(lctx)
						emod.attrib['language'] = lang

						# Append measurement afterward.
						lctx = r.first('f:context')

						ckey = fkey.encode('utf-8')
						join_metrics(doc, metrics, False, project, cname, ckey)
						lxml.etree.cleanup_namespaces(r.element)
						emit(docs, ckey, lxml.etree.tostringlist(doc, method='xml', encoding='utf-8'))
					except Exception as exc:
						# XXX: Reveal exception in document.
						print('factor_xml exception', xis, exc)
			# </if iscomposite>

			if in_tests and rroot is not None:
				rroot.element.attrib['type'] = 'tests'
			join_metrics(rdoc, metrics, in_tests, project, cname, rkey)
			emit(docs, rkey, lxml.etree.tostringlist(rdoc, method='xml', encoding='utf-8'))

def main(inv):
	target, package, *args = inv.args
	if args:
		metrics, = args
	else:
		metrics = None
	del args

	ctx = libdev.Context.from_environment()
	copy(ctx, target, package, metrics)
	sys.exit(0)

if __name__ == '__main__':
	libsys.control(main, libsys.Invocation.system())
