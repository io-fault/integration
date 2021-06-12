"""
# System command access to &.join primary functionality.
"""
import sys
from fault.system import process
from fault.system import files
from fault.project import system as lsf
from .. import join

def main(inv:process.Invocation) -> process.Exit:
	ctxdir, project_name, project_factor, fragments, source, *metas = inv.args
	ctxdir = files.Path.from_path(ctxdir)
	fdd = files.Path.from_path(fragments)
	src = files.Path.from_path(source)

	ctx = lsf.Context()
	pd = ctx.connect(ctxdir)

	# Construct dependency context.
	req = ctx.from_product_connections(pd)
	req.load()
	res = join.Resolution(ctx, ctx, ctx.project(project_name), lsf.types.factor@project_factor)

	j = join.transform(res, fdd, src)
	sys.stdout.writelines(j)
	return inv.exit(0)

if __name__ == '__main__':
	process.control(main, process.Invocation.system())
