"""
# Text construction context initialization.
"""
import itertools

from fault.project import system as lsf
from fault.project import factory

from fault.system import files
from fault.system import factors

from ..host import construction as cc

def text(context, factor='type', name='text.cc'):
	text_cc_vectors = cc.getsource(cc.machines_project, name)
	variants = cc.form_variants('void', 'json', modes=['delineation'])
	txtcc = cc.query.dispatched('text-cc')

	return [
		cc.mksole('ft-text-cc', 'vector.system', txtcc),
		cc.mksole('text-delineate-1', cc.vtype, text_cc_vectors.fs_load()),
		cc.mksole('variants', cc.vtype, variants),
	]

def form_meta_type():
	common = cc.comment("Process intercepted metrics and identity forms.")
	common += cc.define('[factor-type]',
		('', 'http://if.fault.io/factors/meta'),
	) + '\n'
	common += cc.define('[integration-type]',
		('', 'chapter'),
	) + '\n'

	common += cc.define('Translate',
		('fv-form-delineated', '.ft-text-cc -parse-text-1 .text-delineate-1'),
		('fv-form-metrics', '.measure-source -stdio .adapters'),
		('fv-form-identity', '.identify-source -stdio .adapters'),
		('!', '.form-error -error-context .adapters'),
	) + '\n'

	common += cc.define('Render',
		('fv-form-delineated', '.ft-text-cc -store-chapter-1 .text-delineate-1'),
		('fv-form-metrics', '.aggregate-metrics -metrics-join .adapters'),
		('fv-form-identity', '.form-identity -identity-join .adapters'),
		('!', '.form-error -error-context .adapters'),
	) + '\n'

	return common

def meta(context):
	return text(context) + [
		cc.fx('form-error', 'python', '.string', 'exit(1)'),

		cc.fx('measure-source', 'python', 'system.metrics.measure', 'source'),
		cc.fx('aggregate-metrics', 'python', 'system.metrics.aggregate'),
		cc.fx('identify-source', 'python', 'system.tools.identify', 'source', '-'),
		cc.fx('form-identity', 'python', 'system.tools.identify', 'index'),

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
				'[fv-form]',
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

def mkvectors(context, route, name='machines'):
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

def mkcc(route, context_name='machines'):
	mkvectors(context_name, route)
	cc.iproduct(route, [x.route for x in factors.context.product_sequence])
