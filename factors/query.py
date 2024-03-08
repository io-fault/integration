"""
# Manipulate and retrieve product information.
"""
import collections

import sys
import os
import importlib
import contextlib

from fault.vector import recognition
from fault.system import files
from fault.system import process
from fault.project import system as lsf
from fault.transcript.io import Log

from . import __name__ as project_package_name
from . import context

restricted = {
	'-.': ('ignore', None, None),

	# Defaults to never update.
	'--void': ('field-replace', True, 'remove-product-index'),
	'-u': ('field-replace', 'missing', 'update-product-index'),
	'-U': ('field-replace', 'always', 'update-product-index'),
	'-x': ('field-replace', 'missing', 'initialize-system-context'),

	'--summary': ('field-replace', 'summary', 'select-operation'),
}

required = {
	'-X': ('field-replace', 'system-context-directory'),

	'-D': ('field-replace', 'product-directory'),

	'-i': ('sequence-append', 'interpreted-connections'),
	'-s': ('sequence-append', 'interpreted-disconnections'),
	'-I': ('sequence-append', 'direct-connections'),
	'-S': ('sequence-append', 'direct-disconnections'),
}

def sources(factor_record):
	(fpath, ftype), (syms, src) = factor_record
	for x in src:
		yield x[1]

def stats(projects):
	rows = []

	for pj in projects:
		# File size of sources in the project.
		sizes = [[y.fs_size() for y in sources(x)] for x in pj.select(lsf.types.factor)]

		# Calculate factor count, source count, and total size of the sources.
		f_count = len(sizes)
		count = sum(len(x) for x in sizes)
		size = sum(sum(x) for x in sizes)

		rows.append((pj.corpus, pj.identifier, pj.factor, f_count, count, size))

	return rows

def report(exits, meta, log, config, sysctx, pdr, remainder):
	"""
	# Write human readable information about the product and the identified projects.
	"""

	if pdr.fs_type() != 'directory':
		meta.warning("product path is not a directory")
		# Nothing to do. This is not an error.
		raise SystemExit(0)

	ctx = lsf.Context()
	ctx.connect(pdr)
	ctx.load()
	ctx.configure()

	records = stats(ctx.iterprojects())
	p_count = len(records)

	g = collections.defaultdict(list)
	for r in records:
		g[r[0]].append(r)
	c_count = len(g)
	log.write(f"Product directory '{pdr!s}' contains {p_count} projects across {c_count} corpora.\n\n")

	for c, r in g.items():
		cp_count = len(r)
		log.write(f"{c} {cp_count} projects\n")
		for corpus, iid, pj_factor, f_count, src_count, src_size in r:
			fmt = f"  {pj_factor} {f_count} factors {src_count} sources {src_size} bytes {iid}\n"
			log.write(fmt)

switch = {
	'summary': report,
}

def index(pd:lsf.Product, statement):
	"""
	# Update the index according the requested &statement.
	"""

	if statement in {'never', None}:
		return False
	elif statement == 'always':
		# Rebuild
		pd.clear()
	elif statement == 'missing' and pd.cache.fs_type() == 'void':
		pass
	else:
		return False

	pd.update()
	pd.store()
	return True

def connecting(config):
	"""
	# Normalize the interpreted connections and disconnections.
	"""

	ci = []
	cx = []

	ci.extend(str(files.Path.from_path(x)) for x in config.get('interpreted-connections', ()))
	cx.extend(str(files.Path.from_path(x)) for x in config.get('interpreted-disconnections', ()))

	ci.extend(config.get('direct-connections', ()))
	cx.extend(config.get('direct-disconnections', ()))

	return ci, cx

def reconnect(pd:lsf.Product, insertions, deletions):
	"""
	# Update the product's connections.
	"""

	fp = pd.connections_index_route
	cl = []
	try:
		cl.extend(fp.fs_load().decode('utf-8').split('\n'))
	except FileNotFoundError:
		# Essentially empty CONNECTIONS.
		pass

	cl.extend(insertions)
	written = set(deletions)

	f = (lambda x: written.add(x) or x)
	fp.fs_store('\n'.join(f(x) for x in cl if x not in written and x.strip()).encode('utf-8'))

# Rebuild project index from directory structure.
def io(exits, meta, log, config, sysctx, pdr:files.Path, remainder):
	"""
	# Perform requested changes and select requested information.
	"""

	ops = 0
	pd = lsf.Product(pdr)

	if index(pd, config.get('update-product-index', None)):
		ops += 1
		meta.notice("updated project index using the product directory")

	ci, cx = connecting(config)
	if ci or cx:
		ops += 1
		reconnect(pd, ci, cx)

	if config.get('remove-product-index', False):
		ops += 1
		if pd.cache.fs_type() != 'void':
			pd.cache.fs_void()
			meta.notice("product index destroyed")
		else:
			meta.notice("product index does not exist")

	if config['system-context-directory'] is not None:
		sysctx = process.fs_pwd() @ config['system-context-directory']
	else:
		sysctx = pdr/'.system'

	if config['initialize-system-context'] == 'missing':
		if sysctx.fs_type() == 'void':
			# machines.initialize
			ops += 1
			from ..machines import initialize
			initialize.perform(sysctx)
			meta.notice("system context initialized")

		if (pdr/'.system').fs_type() == 'void':
			# Link to configured system context if not available.
			ops += 1
			(pdr/'.system').fs_link_relative(sysctx)
			meta.notice("product system context linked")

	if ops == 0:
		meta.notice("no product manipulations were performed")

	meta.flush()

	if config['select-operation'] is not None:
		switch[config['select-operation']](exits, meta, log, config, sysctx, pdr, remainder)

	return pd

def configure(restricted, required, argv):
	"""
	# Root option parser.
	"""

	config = {
		'machines-context-name': 'machines',
		'system-context-directory': None,
		'initialize-system-context': 'never',
		'construction-mode': 'executable',
		'product-directory': None,

		'interpreted-connections': [],
		'interpreted-disconnections': [],
		'direct-connections': [],
		'direct-disconnections': [],

		'select-operation': None,
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def main(inv:process.Invocation) -> process.Exit:
	pwd = process.fs_pwd()

	config, remainder = configure(restricted, required, inv.argv)

	if config['product-directory']:
		pdr = files.Path.from_path(config['product-directory'])
	else:
		pdr = pwd

	# Identify the system context to use to process factors.
	origin, sysctx = context.resolve(config['system-context-directory'], product=pdr)

	with contextlib.ExitStack() as ctx:
		io(ctx, Log.stderr(), Log.stdout(), config, sysctx, pdr, remainder)
	return inv.exit(0)
