"""
# Construction Context implementation using vector formulations.
"""
import sys
import functools
import itertools
import typing
import collections

from fault.system import files
from fault.system import execution
from fault.project import system as lsf
from fault.vector import formulation as vf

from . import core

def _variant_constants(variants):
	return {
		'fv-intention': variants.form,
		'fv-system': variants.system,
		'fv-architecture': variants.architecture,
		'fv-form': variants.form
	}

def _variant_conclusions(variants):
	return {
		'fv-i' + variants.form,
		'fv-system-' + variants.system,
		'fv-architecture-' + variants.architecture,
		'fv-intention-' + variants.form,
		'fv-form-' + (variants.form or 'void'),
	}

class Mechanism(object):
	"""
	# A section of a construction context that can formulate adapters for factor processing.
	"""

	def __init__(self, context, semantics):
		self.context = context
		self.semantics = semantics
		self._cache = {}

	def __repr__(self):
		return repr((self.context.route, self.semantics))

	def _cc(self, phase, section, variants, itype, xtype):
		k = (phase, section, variants, itype, xtype)
		if k in self._cache:
			return self._cache[k]

		c = self.context.cc_compose(phase, section, variants, itype, xtype)
		self._cache[k] = c
		return c

	def variants(self, intentions):
		"""
		# Generate the full combinations of sections and variants
		# for the given intentions.
		"""
		return self.context.cc_variants(self.semantics, intentions)

	def integrates(self, section, variants, itype):
		"""
		# Identify whether the mechanism is operable.
		"""
		return str(itype) in self.context.cc_integration_types(section, variants, itype)

	def unit_name_delta(self, section, variants, itype):
		"""
		# Identify the prefix and suffix for the unit file.
		"""
		return self.context.cc_unit_name_delta(section, variants, itype)

	def prepare(self, section, variants, itype, srctype):
		"""
		# Construct the command constructor for source preparation.
		"""
		return self._cc('Prepare', section, variants, itype, srctype)

	def translate(self, section, variants, itype, srctype):
		"""
		# Construct the command constructor for translating sources.
		"""
		return self._cc('Translate', section, variants, itype, srctype)

	def render(self, section, variants, itype):
		"""
		# Construct the command constructor for rendering the factor's image.
		"""
		return self._cc('Render', section, variants, itype, None)

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
	def from_directory(Class, route:files.Path, intention:str='optimal'):
		"""
		# Create instance using a directory. Defaults depending intention to (id)`optimal`.
		"""
		return Class(route, intention)

	def __init__(self, route:files.Path, intention:str):
		self.route = route
		# Requirement intention for metadata contexts.
		self.intention = intention
		self.projects = lsf.Context()
		self.intercepts = {}

		# Projection mappings. semantics -> project
		self._idefault = None
		self._icache = {}
		self._vcache = {}

		# Initialization Context for loading projections and variants.
		self._vinit = vf.Context(set(), {})

	def _variants(self, factor):
		"""
		# Read the full product of system-architecture pairs from
		# the given variants &factor.
		"""
		v = self._load_vector(factor)
		for system in self._cat(self._vinit, v, '[systems]'):
			for arch in self._cat(self._vinit, v, '[' + system + ']'):
				yield (system, arch)

	def cc_unit_name_delta(self, section, variants, itype):
		# Unit name adjustments.
		initctx = vf.Context(_variant_conclusions(variants), _variant_constants(variants))
		exe, adapter, idx = self._read_merged(
			initctx,
			section, variants,
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

	def cc_integration_types(self, section, variants, itype):
		# Supported integration types.
		ctx = vf.Context(_variant_conclusions(variants), _variant_constants(variants))
		exe, adapter, idx = self._read_merged(
			ctx, section, variants, 'Render', itype, None
		)
		aft, = (self._cat(ctx, idx, "[factor-type]"))
		return list((aft + '.' + x) for x in self._cat(ctx, idx, "[integration-type]"))

	def cc_variants(self, semantics, intentions):
		"""
		# Identify the variant combinations to use for the given &semantics and &intentions.
		"""
		fvp = list()

		# Identify the set of variants.
		for section in self._idefault[semantics]:
			vfactor = (section @ 'variants')
			spec = [
				(self.intercepts.get(i, section), lsf.types.Variants(x[0], x[1], i))
				for i, x in itertools.product(intentions, self._variants(vfactor))
			]
			fvp.extend(spec)

		return fvp

	def _constants(self, section, variants, itype, xtype, **kw):
		if xtype:
			fmt = xtype.format
			kw.update({'language': fmt.language, 'dialect': fmt.dialect})

		kw['null'] = '/dev/null'
		kw['factor-integration-type'] = str(itype.factor)
		kw.update(_variant_constants(variants))

		from fault.system import identity
		kw['host-system'], kw['host-architecture'] = identity.root_execution_context()
		kw['host-python'] = identity.python_execution_context()[1]

		return kw

	def _conclusions(self, section, variants, itype, xtype):
		if xtype and xtype.isolation:
			fmt = xtype.format
			l = {'language-' + fmt.language, 'dialect-' + (fmt.dialect or '')}
		else:
			l = set()

		return l | {
			'it-' + itype.factor.identifier,
			'cc-' + str(section),
		} | _variant_conclusions(variants)

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
		exeref, adapter, *composition = self._load_descriptor(
			vctx, section, variants, phase, itype, xtype
		)

		idx = {}
		for x in composition:
			vects = self._ref(section, x)
			idx.update(self._v(vects))

		return exeref, adapter, idx

	def cc_compose(self, phase, section, variants, itype, xtype):
		vctx = vf.Context(
			self._conclusions(section, variants, itype, xtype),
			self._constants(section, variants, itype, xtype)
		)
		exeref, adapter, idx = self._read_merged(vctx, section, variants, phase, itype, xtype)

		# Compose command constructor.
		vr = vctx.compose(idx, adapter)
		def Adapt(query, Format=list(vr), Chain=itertools.chain.from_iterable):
			return Chain(x(query) for x in Format)

		return self._load_system(self._ref(section, exeref)), Adapt

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
		for intention in sections_vf.keys():
			v = self._cat(self._vinit, sections_vf, intention)
			for i in v:
				yield intention, context @ i

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
		for section, variants in mech.variants(['debug', 'optimal']):
			print('-->', section, variants)
			plan, vcon = mech.render(section, variants, itype)
			outv = list(vcon(lambda x: r.get(x, ())))
			print(outv)
			print(plan)
