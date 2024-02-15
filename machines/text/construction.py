"""
# Host construction context initialization.
"""
import itertools

from fault.project import system as lsf
from fault.project import factory

from fault.system import files
from fault.system import factors

from ..host import construction as cc

def text(context, factor='type', name='text.cc'):
	text_cc_vectors = cc.getsource(cc.machines_project, name)
	variants = cc.form_variants('void', 'json', forms=['delineated'])
	txtcc = cc.query.dispatched('text-cc')

	return [
		cc.mksole('ft-text-cc', 'vector.system', txtcc),
		cc.mksole('text-delineate-1', cc.vtype, text_cc_vectors.fs_load()),
		cc.mksole('variants', cc.vtype, variants),
	]

def form_meta_type():
	common = cc.comment("Process intercepted metrics and identity intentions.")
	common += cc.define('[factor-type]',
		('', 'http://if.fault.io/factors/meta'),
	) + '\n'
	common += cc.define('[integration-type]',
		('', 'chapter'),
	) + '\n'

	common += cc.define('Translate',
		('fv-intention-delineated', '.ft-text-cc -parse-text-1 .text-delineate-1'),
		('fv-intention-metrics', '.measure-source -stdio .adapters'),
		('fv-intention-identity', '.identify-source -stdio .adapters'),
		('!', '.intention-error -error-context .adapters'),
	) + '\n'

	common += cc.define('Render',
		('fv-intention-delineated', '.ft-text-cc -store-chapter-1 .text-delineate-1'),
		('fv-intention-metrics', '.aggregate-metrics -metrics-join .adapters'),
		('fv-intention-identity', '.form-identity -identity-join .adapters'),
		('!', '.intention-error -error-context .adapters'),
	) + '\n'

	return common

def meta(context):
	return text(context) + [
		cc.fx('intention-error', 'python', '.string', 'exit(1)'),

		cc.fx('measure-source', 'python', 'system.metrics.measure', 'source'),
		cc.fx('aggregate-metrics', 'python', 'system.metrics.aggregate'),
		cc.fx('identify-source', 'python', 'system.factors.identify', 'source', '-'),
		cc.fx('form-identity', 'python', 'system.factors.identify', 'index'),

		cc.mksole('projections', cc.vtype,
			cc.constant('meta', 'http://if.fault.io/factors/meta')
		),
		cc.mksole('adapters', cc.vtype,
			cc.constant('-stdio',
				'"measure-source-file" input output',
			) + \
			cc.constant('-error-context',
				'"unconditional-failure" - -',
				'[factor]',
				'[fv-intention]',
			) + \
			cc.constant('-metrics-join',
				'"aggregate-metrics" - -',
				'[factor-image] [work-directory]',
				'[project-path] [factor-relative-path]',
				'[units]',
			) + \
			cc.constant('-identity-join',
				'"combine-identities" - -',
				'[factor-image]',
				'[units]',
			)
		),
		cc.mksole('type', cc.vtype, form_meta_type()),
	]

def mkvectors(context, route, name='vectors'):
	soles = [
		cc.mksole('bin-cp', 'vector.system', cc.system('/bin/cp')),
		cc.mksole('bin-ln', 'vector.system', cc.system('/bin/ln')),
	]

	# Vectors Context
	pi = cc.mkinfo(context + '.context', name)
	pj = cc.mkctx(pi, cc.formats, route, context, soles)
	cc.factory.instantiate(*pj)

	# Meta. projections, intercepts, and error cases.
	pi = cc.mkinfo(context + '.meta', 'meta')
	pj = cc.mkproject(pi, route, context, 'meta', meta(context))
	cc.factory.instantiate(*pj)

def mkcc(route):
	mkvectors('vectors', route)
	cc.mktools('tools', route)
	cc.iproduct(route, [x.route for x in factors.context.product_sequence])
