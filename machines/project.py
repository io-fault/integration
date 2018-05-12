identity = 'http://fault.io/engineering/adapters/llvm'
name = 'llvm'
abstract = 'LLVM based compilation, delineation, and coverage tools'
icon = '<http://llvm.org>'

versioning = 'continuous'
status = 'flux'

controller = 'fault.io'
contact = 'http://fault.io/critical'

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
