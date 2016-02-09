"""
Document the entire package tree into a
&..filesystem.library.Dictionary instance.
"""

import sys
import itertools
import os.path
import lzma
import types
import importlib.machinery
import pickle

from .. import libpython
from .. import library as libfactors

from ...routes import library as libroutes
from ...eclectic import library as libeclectic
from ...xml import library as libxml
from ...filesystem import library as libfs

def structure_package(target, package, survey=None):
	docs = libfs.Dictionary.create(libfs.Hash(), os.path.realpath(target))
	root, (packages, modules) = libfactors.factors(package)

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

		# build libeclectic.Context for documentation
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
			dm.__type__ = 'chapter' # note as chapter module
			dm.__package__ = rname
			dm.__file__ = f.fullpath
			doc_modules.append(dm.__name__)

			doc_pkg_module.__dict__[basename] = dm
			doc_pkg_module.__type__ = 'documentation'
			sys.modules[dm.__name__] = dm

	iterdocs = map(libroutes.Import.from_fullname, doc_modules)

	for x in itertools.chain((root,), packages, modules, iterdocs):
		query = libpython.Query(x)
		cname = query.canonical(x.fullname)
		module_name = x.fullname.encode('utf-8')

		# Load coverage and profile data regarding the factor.
		tdata = cdata = pdata = None

		if survey is not None:
			# survey data available.

			profile_data = b'profile:' + module_name
			coverage_data = b'coverage:' + module_name
			test_data = b'tests:' + module_name

			if isinstance(survey, str):
				survey = libfs.Dictionary.open(survey)

			if survey.has_key(profile_data):
				with survey.route(profile_data).open('rb') as f:
					try:
						pdata = pickle.load(f)
					except EOFError:
						pdata = None

			if survey.has_key(coverage_data):
				with survey.route(coverage_data).open('rb') as f:
					try:
						cdata = pickle.load(f)
					except EOFError:
						cdata = None

			if survey.has_key(test_data):
				# only matches with project packages
				with survey.route(test_data).open('rb') as f:
					try:
						tdata = pickle.load(f)
					except EOFError:
						tdata = None

		query.parameters['profile'] = pdata
		query.parameters['coverage'] = cdata
		dociter = libpython.document(query, x, survey=survey)

		key = cname.encode('utf-8')
		r = docs.route(key)
		r.init('file')
		deflate = lzma.LZMACompressor()
		deflate = None

		with r.open('wb') as f:
			# the xml declaration prefix is not written.
			# this allows stylesheet processing instructions
			# to be interpolated without knowning the declaration
			# size.
			if deflate:
				f.write(deflate.compress(b''.join((dociter))))
				f.write(deflate.flush())
			else:
				f.write(b''.join((dociter)))

	return 0

if __name__ == '__main__':
	sys.exit(structure_package(*sys.argv[1:]))
