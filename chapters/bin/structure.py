"""
# Extract the structure of the entire package tree into a
# &..filesystem.library.Dictionary instance.
"""

import sys
import itertools
import os.path
import lzma
import types
import importlib.machinery
import pickle

from .. import python
from .. import library as libfactors

from ...system import libfactor
from ...routes import library as libroutes
from ...text import library as libtext
from ...xml import libfactor as xmlfactor
from ...filesystem import library as libfs

from ...chronometry import library as libtime

def load_metrics(metrics, key):
	profile_data = b'profile:' + key
	coverage_data = b'coverage:' + key
	test_data = b'tests:' + key

	pdata = cdata = tdata = None

	if metrics.has_key(profile_data):
		with metrics.route(profile_data).open('rb') as f:
			try:
				pdata = pickle.load(f)
			except EOFError:
				pdata = None

	if metrics.has_key(coverage_data):
		with metrics.route(coverage_data).open('rb') as f:
			try:
				cdata = pickle.load(f)
			except EOFError:
				cdata = None

	if metrics.has_key(test_data):
		# only matches with project packages
		with metrics.route(test_data).open('rb') as f:
			try:
				tdata = pickle.load(f)
			except EOFError:
				tdata = None

	return pdata, cdata, tdata

def structure_package(target, package, metrics=None):
	docs = libfs.Dictionary.create(libfs.Hash(), os.path.realpath(target))
	root, (packages, modules) = libfactors.factors(package)

	if metrics is not None and isinstance(metrics, str):
		metrics = libfs.Dictionary.open(metrics)

	doc_modules = []
	# &.documentation packages are handled specially.
	# `.txt` files are processed in the context of their
	# containing project.
	for pkg in packages:
		td = pkg / 'documentation'
		if not td.exists():
			continue
		dr = td.directory()
		doc_pkg_module = td.module()

		dirs, files = dr.subnodes()
		rname = td.fullname
		subs = doc_pkg_module.__submodules__ = []

		# build libtext.Context for documentation
		for f in files:
			if f.extension != 'txt':
				continue

			# process text file
			basename = f.identifier[:len(f.identifier)-4]
			subs.append(basename)
			#path = '.'.join((qname, basename))
			#tr = docs.route(path.encode('utf-8'))

			# the module representation is used so we can use the
			# normal processing context for our text files. (reference namespaces)

			dm = types.ModuleType(rname + '.' + basename)
			dm.__factor_domain__ = 'documentation'
			dm.__factor_type__ = 'chapter' # note as chapter module
			dm.__package__ = rname
			dm.__file__ = f.fullpath
			doc_modules.append(dm.__name__)

			doc_pkg_module.__dict__[basename] = dm
			sys.modules[dm.__name__] = dm

		doc_pkg_module.__factor_domain__ = 'documentation'
		doc_pkg_module.__factor_type__ = 'book'

	iterdocs = map(libroutes.Import.from_fullname, doc_modules)

	factors = [
		(x, python.Query(x), x.fullname.encode('utf-8'))
		for x in itertools.chain((root,), packages, modules, iterdocs)
	]

	# The Python module level is processed independently;
	fractions = libfactors.fractions(packages)

	from ...llvm import xslt
	from ...development import library as libdev
	xslt_doc, xslt_transform = xmlfactor.xslt(xslt)

	devctx = libdev.Context.from_environment()

	for x, query, module_name in itertools.chain(factors):
		cname = query.canonical(x.fullname)
		key = cname.encode('utf-8')

		module = x.module()
		if libfactor.composite(x):
			module.__factor_composite__ = True
		else:
			module.__factor_composite__ = False

		# Load coverage and profile data regarding the factor.
		if metrics is not None:
			pdata, cdata, tdata = load_metrics(metrics, key)
		else:
			tdata = cdata = pdata = None

		query.parameters['profile'] = pdata
		query.parameters['coverage'] = cdata
		dociter = python.document(query, x, module, metrics=metrics)

		python.emit(docs, key, dociter)

		# Composites have a set of subfactors,
		# build special module instances that can be processed by python.document().
		if module.__factor_composite__:
			is_ext = libfactor.python_extension(module)
			f = libdev.Factor(None, module, None)

			vars, mech = devctx.select(f.domain)
			refs = libdev.references(f.dependencies())

			f_sources = list(f.link(dict(vars), devctx, mech, refs, ()))
			if not f_sources:
				# XXX: Use an empty directory and continue.
				# Note the absence of data instead of skipping.
				continue
			(sp, (vl, key, loc)), = f_sources

			dirs, sources = loc['integral'].tree()
			iformat = 'xml'
			index = loc['integral']
			xi = (index / 'out') / iformat

			sources = libfactor.sources(x)
			prefix = str(sources)
			prefix_len = len(prefix)

			# A target module that has a collection of sources.
			# Identify the source tree and find the interface description.
			srctree = sources.tree()
			for y in srctree[1]:
				if y.identifier.startswith('.'):
					# Ignore dot files.
					continue

				sfm = types.ModuleType(module.__name__, "")
				sfm.__file__ = str(y)
				sfm.__factor_language__ = libdev.languages.get(y.extension)
				sfm.__factor_composite__ = False
				sfm.__factor_domain__ = 'unit'
				sfm.__factor_composite_type__ = module.__factor_type__
				suffix = sfm.__factor_path__ = str(y)[prefix_len+1:]
				sfm.__factor_key__ = (cname + '/' + sfm.__factor_path__)
				sfm.__directory_depth__ = sfm.__factor_key__.count('/')

				xis = os.path.join(str(index), suffix)
				try:
					sfm.__factor_xml__ = xmlfactor.transform(xslt_transform, xis)[1]
				except Exception as exc:
					# XXX: Reveal exception in document.
					exc.__traceback__ = None
					sfm.error = exc
					sfm.file = xis
					sfm.__factor_xml__ = None
					print('factor_xml exception', xis)

				if metrics is not None:
					pdata, cdata, tdata = load_metrics(metrics, sfm.__factor_key__.encode('utf-8'))
				else:
					tdata = cdata = pdata = None
				query.parameters['profile'] = pdata
				query.parameters['coverage'] = cdata

				dociter = python.document(query, x, sfm, metrics=metrics)
				python.emit(docs, sfm.__factor_key__.encode('utf-8'), dociter)

if __name__ == '__main__':
	structure_package(*sys.argv[1:])
	sys.exit(0)
