"""
# Construction Context implementation using vector formulations.
"""
import sys
import functools
import itertools
import typing
import collections
from dataclasses import dataclass

from fault.context import tools
from fault.system import files
from fault.system import execution
from fault.project import system as lsf
from fault.vector import formulation as vf

from . import core

@dataclass(eq=True, unsafe_hash=True)
class Void(Exception):
	"""
	# Raised when a empty vector is composed, but more than
	# zero fields are required by the caller.

	# [ Properties ]
	# /v_type/
		# A classification identifier for the type of request that caused the exception.
	# /v_required/
		# The minimum number of fields required by the caller.
	"""
	v_type: str
	v_required: int = 1

	def __str__(self):
		return f"{self.v_type!r} inquery requires {self.v_required} fields"

def _feature_constants(features):
	return {'if-set': features}

def _feature_conclusions(features):
	return frozenset(['if-' + f for f in features])

def _variant_constants(variants):
	return {
		'fv-system': variants.system,
		'fv-architecture': variants.architecture,
		'fv-form': variants.form
	}

def _variant_conclusions(variants):
	return {
		'fv-system-' + variants.system,
		'fv-architecture-' + variants.architecture,
		'fv-form-' + (variants.form or 'void'),
	}

@tools.struct()
class VectorParameters(object):
	mode: str
	section: str
	variants: lsf.types.Variants
	features: list[str]

	def constants(self):
		return {
				'cc-mode': str(self.mode),
				'fi-section': str(self.section),
			} | \
			_variant_constants(self.variants) | \
			_feature_constants(self.features)

	def conclusions(self):
		return {
				'cc-mode-' + str(self.mode),
				'fi-' + str(self.section),
			} | \
			_variant_conclusions(self.variants) | \
			_feature_conclusions(self.features)

	def context(self):
		return self.conclusions(), self.constants()

class Mechanism(object):
	"""
	# A section of a construction context that can formulate adapters for factor processing.
	"""

	def __init__(self, context, mode, semantics):
		self.context = context
		self.mode = mode
		self.semantics = semantics
		self._cache = {}

	def __repr__(self):
		return repr((self.context.route, self.semantics))

	def _cc(self, phase, vtype, itype, xtype):
		k = (phase, vtype.section, vtype.variants, itype, xtype)
		if k in self._cache:
			return self._cache[k]

		c = self.context.cc_compose(phase, vtype, itype, xtype)
		self._cache[k] = c
		return c

	def vectortypes(self, features):
		"""
		# Identify formulation types for the given form and feature set.
		"""
		return list(self.context.vectortypes(self.mode, self.semantics, features))

	def integrates(self, vtype, itype):
		"""
		# Identify whether the mechanism is operable.
		"""
		try:
			return str(itype) in self.context.cc_integration_types(vtype, itype)
		except KeyError:
			# No constraints expressed by vectors.
			return True

	def unit_name_delta(self, vtype, itype):
		"""
		# Identify the prefix and suffix for the unit file.
		"""
		try:
			return self.context.cc_unit_name_delta(vtype, itype)
		except Void:
			# Allow unspecified extensions.
			return "", ""

	def prepare(self, vtype, itype, srctype):
		"""
		# Construct the command constructor for source preparation.
		"""
		return self._cc('Prepare', vtype, itype, srctype)

	def translate(self, vtype, itype, srctype):
		"""
		# Construct the command constructor for translating sources.
		"""
		return self._cc('Translate', vtype, itype, srctype)

	def render(self, vtype, itype):
		"""
		# Construct the command constructor for rendering the factor's image.
		"""
		return self._cc('Render', vtype, itype, None)

class Context(object):
	"""
	# Vectors Formulations based Mechanism set for building system argument vectors.
	"""

	@staticmethod
	def _ref(section, name):
		if name[:2] == '..':
			# Context relative.
			ref = section.container @ name[2:]
		elif name[:1] == '.':
			# Project relative.
			ref = section @ name[1:]
		else:
			# Unqualified, absolute.
			ref = lsf.types.factor @ name

		return ref

	@classmethod
	def from_directory(Class, route:files.Path):
		"""
		# Create instance using a directory.
		"""
		return Class(route)

	def __init__(self, route:files.Path):
		self.route = route
		self.projects = lsf.Context()
		self.intercepts = {}

		# Projection mappings. semantics -> project
		self._idefault = None
		self._icache = {}
		self._vcache = {}

		# Initialization Context for loading projections and variants.
		self._vinit = vf.Context(set(), {})

	def _modes(self, factor):
		"""
		# Read the modes vector from factor.
		"""

		try:
			v = self._load_vector(factor)
		except LookupError:
			return []

		return list(self._cat(self._vinit, v, '[modes]'))

	def _variants(self, factor):
		"""
		# Read the full product of system-architecture pairs from
		# the given variants &factor.
		"""
		v = self._load_vector(factor)
		for system in self._cat(self._vinit, v, '[systems]'):
			for arch in self._cat(self._vinit, v, '[' + system + ']'):
				yield (system, arch)

	def cc_unit_name_delta(self, vtype, itype):
		# Unit name adjustments.
		initctx = vf.Context(*vtype.context())
		exe, adapter, idx = self._read_merged(
			initctx,
			vtype.section, vtype.variants,
			'Render', itype, None
		)

		try:
			unit_prefix = list(self._cat(initctx, idx, "[unit-prefix]"))[0]
		except KeyError:
			unit_prefix = ""

		try:
			unit_suffix = list(self._cat(initctx, idx, "[unit-suffix]"))[0]
		except KeyError:
			unit_suffix = ""

		return unit_prefix, unit_suffix

	def cc_integration_types(self, vtype, itype):
		# Supported integration types.
		ctx = vf.Context(*vtype.context())
		try:
			exe, adapter, idx = self._read_merged(
				ctx, vtype.section, vtype.variants, 'Render', itype, None
			)
		except Void:
			# Must support rendering.
			return []

		aft, = (self._cat(ctx, idx, "[factor-type]"))
		return list((aft + '.' + x) for x in self._cat(ctx, idx, "[integration-type]"))

	def vectortypes(self, mode, semantics, features):
		"""
		# Identify the &VectorParameter combinations to use for the given &semantics and &modes.
		"""

		# Identify the set of variants.
		for section in self._idefault[semantics]:
			# The original section provides the variants and the intercepts
			# redirect the section when a mode matches one in the mapping.
			vfactor = (section @ 'variants')

			if mode in self.intercepts:
				applied, reform, fmode = self.intercepts[mode]

				if fmode == '.':
					fmode = mode

				if applied == '.':
					applied = section
				else:
					applied = (section * applied)

				if reform == '.':
					reform = mode
			else:
				applied = section
				reform = mode
				fmode = mode

			if fmode not in self._modes(section @ 'variants'):
				continue

			# Construct vtype instances for each variant replacing the section
			# with the intercept's substitution.
			for x in self._variants(vfactor):
				yield VectorParameters(mode, applied, lsf.types.Variants(x[0], x[1], reform), features)

	def _constants(self, vtype, itype, xtype, **kw):
		if xtype:
			fmt = xtype.format
			kw.update({'language': fmt.language, 'dialect': fmt.dialect})

		kw['null'] = '/dev/null'
		kw['factor-integration-type'] = str(itype.factor)
		kw.update(vtype.constants())

		from fault.system import identity
		kw['host-system'], kw['host-architecture'] = identity.root_execution_context()
		kw['host-python'] = identity.python_execution_context()[1]

		return kw

	def _conclusions(self, vtype, itype, xtype):
		if xtype and xtype.isolation:
			fmt = xtype.format
			l = {'language-' + fmt.language, 'dialect-' + (fmt.dialect or '')}
		else:
			l = set()

		return l | {
			'it-' + itype.factor.identifier,
		} | vtype.conclusions()

	def _compose(self, vctx, section, composition, itype, name, fallback):
		idx = {}
		for c in composition:
			idx.update(self._load_vector(section @ c).items())

		try:
			idx.update(self._load_vector(section @ itype.factor.identifier).items())
		except LookupError:
			pass

		# Catenate the vectors selected in index using _vinit.
		if name in idx:
			return vctx.chain(self._iq, idx, name)
		else:
			return vctx.chain(self._iq, idx, fallback)

	def _load_descriptor(self, vctx, section, variants, phase, itype, xtype):
		k = (phase, variants, itype, xtype)

		if itype.isolation is not None:
			prefix = (itype.isolation,)
		else:
			prefix = ('type',)

		if k not in self._vcache:
			fall = phase
			if xtype:
				name = phase + '-' + xtype.isolation.split('.', 1)[0]
			else:
				name = phase
				if itype.isolation:
					name += '-' + itype.isolation

			self._vcache[k] = list(self._compose(vctx, section, prefix, itype, name, fall))

		return self._vcache[k]

	def _read_merged(self, vctx, section, variants, phase, itype, xtype):
		vector = self._load_descriptor(vctx, section, variants, phase, itype, xtype)
		if len(vector) == 0:
			# Empty
			raise Void('composition', 2)

		exeref, adapter, *composition = vector
		idx = {}
		for x in composition:
			vects = self._ref(section, x)
			idx.update(self._v(vects))

		return exeref, adapter, idx

	def cc_compose(self, phase, vtype, itype, xtype):
		vctx = vf.Context(
			self._conclusions(vtype, itype, xtype),
			self._constants(vtype, itype, xtype)
		)
		exeref, adapter, idx = self._read_merged(vctx, vtype.section, vtype.variants, phase, itype, xtype)

		# Compose command constructor.
		vr = vctx.compose(idx, adapter)
		def Adapt(query, Format=list(vr), Chain=itertools.chain.from_iterable):
			return Chain(x(query) for x in Format)

		return self._load_system(self._ref(vtype.section, exeref)), Adapt

	def _load_intercepts(self,
			context:lsf.types.FactorPath,
			Intercepts='meta.intercepts'
		):
		# Identify the projects providing adapters for the listed semantics.

		f = context @ Intercepts

		# Load .context.intercepts vectors.
		sections_vf = self._v(f)
		if sections_vf is None:
			return

		# Map semantics identifier to the adapter projects in cc.
		for mode in sections_vf.keys():
			v = self._cat(self._vinit, sections_vf, mode)
			yield (mode, tuple(v))

	def load(self):
		"""
		# Load the product indicies.
		"""
		self.projects.connect(self.route)
		self.projects.load()
		self.projects.configure()
		return self

	def configure(self, context=(lsf.types.factor@'vectors')):
		"""
		# Load the default factor semantics.
		"""
		self._idefault = self._map_factor_semantics(context)
		self.intercepts.clear()
		self.intercepts.update(self._load_intercepts(lsf.types.factor@'vectors'))
		return self

	def _read_cell(self, factor):
		"""
		# Get the sole source type and path of the given &factor.
		"""
		try:
			product, project, fp = self.projects.split(factor)
		except LookupError:
			raise LookupError(factor)

		for (name, ft), fd in project.select(fp.container):
			if name == fp:
				syms, srcs = fd
				first, = srcs #* Cell
				return first

	def _load_vector(self, factor):
		"""
		# Load vector formulations from the &factor.
		"""
		c = self._read_cell(factor)
		if c is None:
			raise LookupError(factor)
		return vf.parse(c[1].fs_load().decode('utf-8'))

	def _load_system(self, factor):
		"""
		# Load system command vector identified by &factor.
		"""
		try:
			typ, src = self._read_cell(factor)
		except Exception as error:
			raise LookupError(factor) from error

		return execution.parse_sx_plan(src.fs_load().decode('utf-8'))

	def _iq(self, name):
		# Vector Reference Query method used during initialization.
		return ()

	def _cat(self, ctx, index, name, fallback=None):
		"""
		# Catenate the vectors selected in &index.
		"""
		if name in index:
			return ctx.chain(self._iq, index, name)
		else:
			return ctx.chain(self._iq, index, fallback)

	def _v(self, factor):
		# Cached load vector.
		if factor not in self._vcache:
			self._vcache[factor] = self._load_vector(factor)

		return self._vcache[factor]

	def _map_factor_semantics(self,
			context:lsf.types.FactorPath,
			Projections='meta.projections'
		):
		"""
		# Identify the projects providing adapters for the listed semantics.
		"""

		idx = collections.defaultdict(list)
		f = context @ Projections

		# Load ctx.context.projections vectors.
		# project name -> factor semantics
		pvector = self._v(f)
		if pvector is None:
			return None

		# Map semantics identifier to the adapter projects in cc.
		for project in pvector.keys():
			v = self._cat(self._vinit, pvector, project)
			for i in v:
				idx[i].append(context @ project)

		return idx

if __name__ == '__main__':
	r = {
		'input': ['file.o'],
		'output': ['file.exe'],
	}
	ctx = Context.from_directory(files.root@sys.argv[1]).load().configure()

	fit = 'executable'
	itype = lsf.types.Reference(
		'http://if.fault.io/factors', lsf.types.factor@'system.executable',
		'integration-type', None
	)
	stype = lsf.types.Reference(
		'http://if.fault.io/factors', lsf.types.factor@'system.type',
		'type', 'c.1999'
	)
	mech = Mechanism(ctx, 'http://if.fault.io/factors/system')
	print(repr(mech))
	for i in range(1):
		for vtype in mech.vectortypes(['debug', 'optimal']):
			print('-->', vtyep.section, vtype.variants)
			plan, vcon = mech.render(section, variants, itype)
			outv = list(vcon(lambda x: r.get(x, ())))
			print(outv)
			print(plan)
