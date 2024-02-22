"""
# Factor Execution tools for supporting &.bin.switch.
"""
from dataclasses import replace

from fault.context import tools
from fault.system import files

from fault.project.system import Context
from fault.project.types import Variants
from fault.system.execution import Platform

class IntegrationError(Exception):
	"""
	# An issue with the integration of a project was identified.
	"""

def project_environment(project, factor):
	"""
	# Construct a sequence of environment variables describing the executing factor.
	"""
	return [
		('FACTOR', '.'.join((str(project.factor), str(factor)))),
		('F_PRODUCT', str(project.product.route)),
		('F_PROJECT', str(project.factor)),
		('F_PATH', str(factor)),
		('F_IDENTIFIER', '/'.join((str(project.identifier), str(factor)))),
	]

def image_environment(variants, image):
	"""
	# Construct a sequence of environment variables describing the factor's image.
	"""
	return [
		('F_SYSTEM', variants.system),
		('F_ARCHITECTURE', variants.architecture),
		('F_IMAGE', str(image)),
	]

@tools.cachedcalls(8)
def _cvar(v, a, replace=replace):
	return replace(v, architecture=a)

def image(resolve, factor, variants, architectures, /, _cvar=_cvar):
	"""
	# Identify the image and variants of the project's factor by scanning
	# the filesystem for the given sequence of architectures.
	"""
	for arch in architectures:
		v = _cvar(variants, arch)
		i = resolve(v, factor) # project.image()
		if i.fs_type() != 'void':
			return (v, i)

del _cvar, replace

def plan(execution:Platform, project, factor, variants, image, argv):
	"""
	# Plan the execution of a factor using the &execution platform.
	# Returns a triple suitable for use with &..system.execution.KInvocation.
	"""
	env = project_environment(project, factor) + image_environment(variants, image)
	qfp = str(project.factor + factor)
	envvars, exe_path, xargv = execution.prepare(variants.architecture, qfp, argv)
	env.extend(envvars)
	return (env, exe_path or str(image), xargv)

def select(
		execution:Platform,
		projects:Context,
		factor:str, argv,
		/,
		architecture=None,
		form='',
	):
	"""
	# Identify the appropriate &plan for executing the &factor in &projects
	# using a runtime identified by the &execution platform.
	"""
	pd, pj, fp = projects.split(factor)
	v = Variants(execution.system, architecture, form=form)

	# Scan for integrals executable by the platform in priority order.
	try:
		if architecture is not None:
			# Presume.
			i = pj.image(v, fp)
		else:
			# Scan.
			v, i = image(pj.image, fp, v, execution.architectures)
	except (ValueError, TypeError):
		raise IntegrationError("no architecture available for the selected factor")

	return plan(execution, pj, fp, v, i, argv)
