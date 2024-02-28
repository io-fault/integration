#!/usr/bin/env fault-tool cc -pyc-reduce-1 -pyc-ast-1
##

[protocol]:
	: http://if.fault.io/project/integration.vectors

[unit-suffix]:
	cc-mode-delineation:
		# Delineation, no extension.
		: ""
	!:
		# Executable imaging.
		: ".ast"

[factor-type]:
	: http://if.fault.io/factors/python

[integration-type]:
	: module
	: interface

-cpy-optimize:
	if-optimal:
		: 2
	!:
		if-debug:
			: 0
		!:
			: 1

-pyc-ast-1:
	: "interpret-ast" - -
	: [unit File]
	: [source File]
	cc-mode-delineation:
		: delineated json
	: factor [factor-path]
	: format [language].[dialect]
	: cpython-optimize [-cpy-optimize]
	if-coverage: instrumentation coverage
	: metrics-trap [telemetry-directory File]

-pyc-reduce-1:
	: "compile-bytecode" - -
	: [factor-image File]
	:
		cc-mode-delineation:
			: [unit-directory File]
			: delineated archive
		!: [unit File]
	: format python.ast
	: metrics-trap [telemetry-directory File]
