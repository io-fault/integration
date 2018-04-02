identity = 'http://fault.io/src/python/fragments/llvm'
name = 'llvm'
abstract = 'Delineation and coverage tools for system factors'
icon = '<http://llvm.org>'

fork = 'green'
versioning = 'continuous'
status = 'flux'

controller = 'fault.io'
contact = 'mailto:critical@fault.io'

types = {
	'instrumentation': 'extension',
	'inspection': 'executable',
}

parameters = {
	# For bin.delineate.
	'clang-library-path':
		"Path to the libclang to use.",
	'clang-includes-path':
		"Path to include directory containing libclang headers.",

	# For llvm.instr extension module.
	'llvm-config':
		"The `llvm-config` executable to extract location information from.",
	'llvm-profdata':
		"The profile data command to use in order to process snapshots.",
}
