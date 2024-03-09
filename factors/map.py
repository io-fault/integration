"""
# Factor mapping tool for performing processing of factors with executable factors.
"""
import os
import contextlib
from collections.abc import Sequence
from typing import Callable

from fault.context import tools
from fault.system import process
from fault.system import files
from fault.vector import recognition

from fault.transcript import terminal
from fault.transcript import execution
from fault.transcript.io import Log

from fault.system.execution import KInvocation
from fault.project import system as lsf

from ..root import query
from .context import resolve
from . import filters

def frame_type(sft):
	if sft == 'processing-units':
		from fault.transcript import proctheme as theme
	elif sft == 'test-fates':
		from fault.transcript import fatetheme as theme
	else:
		from fault.transcript import proctheme as theme
	return theme

restricted = {
	'--opened-frames': ('field-replace', True, 'opened-frames'),
	'--closed-frames': ('field-replace', False, 'opened-frames'),
}

required = {
	'--status-type': ('field-replace', 'status-frame-type'),
	'-T': ('sequence-append', 'factor-types'),
	'-L': ('field-replace', 'processing-lanes'),

	'-A': ('field-replace', 'execution-factor'),

	'-X': ('field-replace', 'execution-directory'),
	'-D': ('field-replace', 'product-directory'),
}

def FilterType(pj: lsf.Project, fp: lsf.types.FactorPath, ft: lsf.types.Reference) -> bool:
	return False

@tools.struct()
class Controls(object):
	"""
	# Parameters required for performing and customizing the map operation.
	"""

	ctl_log: Log
	ctl_meta: Log
	ctl_execution_product: files.Path
	ctl_execution_factor: str

	ctl_plan: Callable[[object, object], object]
	ctl_argv: list[str] = ()
	ctl_filter: Callable[[lsf.Project, lsf.types.FactorPath, lsf.types.Reference], bool] = FilterType
	ctl_operation_identifier: str = 'map-operation'
	ctl_open_title: str = 'Operation Aggregate'
	ctl_operating_title: str = 'Operation Aggregate'
	ctl_close_title: str = 'Operation Aggregate'
	ctl_transcript_type: str = 'processing-units'
	ctl_lanes: int = 4
	ctl_display_limit: int = 4
	ctl_opened_frames: bool = True
	ctl_factor_types: set[str] = None

def plan_select(factors:lsf.Context, ctl:Controls, selection):
	"""
	# Create an invocation for processing the project from &factors selected using &selection.
	"""

	try:
		pd, pj, rfp = factors.split(lsf.types.factor@selection)
	except LookupError:
		return

	exeenv, exepath, xargv = query.dispatch('python')
	env = dict(os.environ)
	env.update(exeenv)
	xargv.append('-d')
	xargv.append(ctl.ctl_execution_factor)
	filtered = ctl.ctl_filter

	project = pj.factor
	pj_fp = str(project)
	env['F_PROJECT'] = pj_fp
	env['F_PRODUCT'] = str(ctl.ctl_execution_product)

	if ctl.ctl_factor_types is not None:
		def typefilter(project, fp, ft, *, Inner=filtered, FilterSet=ctl.ctl_factor_types):
			if str(ft) not in FilterSet:
				return True
			else:
				return Inner(project, fp, ft)
		filtered = typefilter

	for (fp, ft), fd in pj.select(rfp):
		if filtered(project, fp, ft):
			continue

		fpstr = str(fp)
		xid = '/'.join((pj_fp, fpstr))

		cmd = xargv + ctl.ctl_argv + [pj_fp, fpstr]
		ki = KInvocation(cmd[0], cmd, environ=env)

		yield (pj_fp, (fpstr,), xid, ki)

def plan_project(factors:lsf.Context, ctl:Controls, selection):
	"""
	# Create an invocation for processing &pj with &cc.
	"""

	pj = factors.project(selection)
	project = pj.factor
	pdr = pj.product.route
	pj_fp = str(project)

	env, exepath, xargv = query.dispatch('factors-cc')
	ki = KInvocation(xargv[0], xargv + ctl.ctl_argv + [str(pdr), pj_fp])

	yield (pj_fp, (), pj_fp, ki)

def construct_arguments(
		cc:files.Path,
		ccmode:str,
		factors:lsf.Context,
		features:Sequence[str],
		cachetype:str,
		cachepath:files.Path,
		identifier,
	):
	return [
		str(cc), ccmode,
		cachetype, str(cachepath),
		':'.join(features),
	]

def execute(exits, op:Controls, queue):
	"""
	# Execute the configured map operation described in &op
	"""

	# Allocate and configure control and monitors.
	control = terminal.setup()
	control.configure(op.ctl_lanes+1) # +1 for the dedicated summary.
	theme = frame_type(op.ctl_transcript_type) # Column labels and units.
	monitors, summary = terminal.aggregate(control, theme, op.ctl_lanes, width=160)

	try:
		op.ctl_log.xact_open(op.ctl_operation_identifier, op.ctl_open_title, {})

		execution.dispatch(
			op.ctl_meta, op.ctl_log,
			tools.partial(op.ctl_plan, op),
			control, monitors, summary,
			op.ctl_operating_title, queue,
			opened=op.ctl_opened_frames
		)
	finally:
		close_msg = control.render_status_text(summary, op.ctl_close_title)
		op.ctl_log.xact_close(op.ctl_operation_identifier, close_msg, {})
		control.clear()
		control.flush()

def configure(restricted, required, argv):
	config = {
		'processing-lanes': '4',
		'product-directory': None,
		'system-context-directory': None,
		'execution-directory': None,
		'execution-factor': 'system.factors.echo',
		'status-frame-type': 'processing-factors',
		'factor-types': [],
		'opened-frames': False,
	}

	oeg = recognition.legacy(restricted, required, argv)
	remainder = recognition.merge(config, oeg)

	return config, remainder

def main(inv:process.Invocation) -> process.Exit:
	config, remainder = configure(restricted, required, inv.argv)

	if config['product-directory'] is not None:
		pdr = process.fs_pwd() @ config['product-directory']
	else:
		pdr = process.fs_pwd()

	if config['execution-directory'] is not None:
		xdr = process.fs_pwd() @ config['execution-directory']
	else:
		xdr = pdr

	# Identify the system context to use to process factors.
	origin, systemctx = resolve(config['system-context-directory'], product=xdr)

	# Configured Factor Context
	factors = lsf.Context()
	factors.connect(pdr)
	factors.load()
	factors.configure()

	ctl = Controls(
		Log.stdout(), Log.stderr(),
		xdr, config['execution-factor'],
		ctl_plan = tools.partial(plan_select, factors),
		ctl_argv = [],
		ctl_transcript_type = config['status-frame-type'],
		ctl_lanes = int(config['processing-lanes']),
		ctl_opened_frames = config['opened-frames'],
		ctl_factor_types = set(config['factor-types']) or None,
	)

	q = filters.SQueue(remainder)
	with contextlib.ExitStack() as ctx:
		execute(ctx, ctl, q)

	return inv.exit(0)
