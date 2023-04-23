"""
# Read the documentation provided by a delineated factor.
"""
import sys
import json

from fault.vector import recognition
from fault.system import files
from fault.system import process
from fault.system import execution
from fault.project import system as lsf

variants = lsf.types.Variants('void', 'json', 'delineated')

def find(project, factor):
	sf = str(factor)
	sp = str(project.factor)

	for fi, fd in project.select(factor**1):
		fp, ft = fi
		if fp != factor:
			continue
		if str(ft) != 'http://if.fault.io/factors/meta.chapter':
			continue

		fmt, file = fd[1][0]
		i = project.image(variants, fp) / file.identifier

		ctx = json.loads((i / 'context.json').fs_load().decode('utf-8'))
		if ctx['protocol'] == 'http://if.fault.io/chapters/system.manual':
			manual(fp, ctx, i)
		else:
			sys.stderr.write(f"ERROR: chapter {sf!r} in project {sp!r} is not a system manual.\n")
			raise SystemExit(2)
		break
	else:
		# No such factor.
		sys.stderr.write(f"ERROR: no such chapter {sf!r} in project {sp!r}.\n")
		raise SystemExit(1)

def manual(factor, context, fs):
	"""
	# Read system manuals from chapter elements.
	"""
	from .manual import transform, prepare

	chapter_path = (fs / 'elements.json')
	chapter_json = chapter_path.fs_load().decode('utf-8')
	chapter = prepare(json.loads(chapter_json)[1][0])
	del chapter_json

	with files.root.fs_tmpdir() as d:
		man_section = chapter[-1]['context']['section']
		man_file = (d / 'rmp').suffix('.'+man_section.sole[1])
		with man_file.fs_open('w') as f:
			f.writelines(
				x + '\n' for x in transform('', chapter)
			)
		ki = execution.KInvocation('/usr/bin/man', ['/usr/bin/man', str(man_file)])
		xdelta = execution.reap(ki.spawn([(0, 0), (1, 1), (2, 2)]), options=0)

restricted = {}
required = {
	'-D': ('set-add', 'product-paths'),
}

def main(inv:process.Invocation) -> process.Exit:
	config = {
		'product-paths': set(),
	}

	v = recognition.legacy(restricted, required, inv.argv)
	factor, = recognition.merge(config, v)

	# Use pwd as product path if none are given.
	productpaths = map(
		process.fs_pwd().__matmul__,
		config['product-paths'] or set('.'),
	)

	# Build factor context for the target product.
	fc = lsf.Context()
	products = list(map(fc.connect, productpaths))
	fc.load()
	fc.configure()

	find(*fc.split(factor)[1:])
	return inv.exit(0)
