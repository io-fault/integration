/**
	// Support macros for Construction Context controlled
	// initialization and termination of instantiated executables.

	// Primarily used by metrics contexts needing to inject measurement
	// collection routines into the start and stop of a program.
*/

/**
	// Default is no tooling. Most contexts perform no injection.
*/
#define FAULT_EXECUTABLE_START(name) name

#define FAULT_EXECUTABLE_ENTER(program_name)
#define FAULT_EXECUTABLE_EXIT(exit_status)

#if FV_INJECTIONS()
	/**
		// Under an injections construction context, main is wrapped so that
		// measurement tooling may be hooked into an executable.
		// Primarily, records of the execution of a metrics process needs to be stored
		// so that the extensions (fragments.llvm) can be used to collect information
		// about those processes.
	*/
	#undef FAULT_EXECUTABLE_ENTER
	#undef FAULT_EXECUTABLE_EXIT

	#define FAULT_EXECUTABLE_ENTER(...) _fault_note_execution_enter(__VA_ARGS__)
	#define FAULT_EXECUTABLE_EXIT(s) _fault_note_execution_exit(s)

	/**
		// Rename "main" as "_fault_application_main".
		// &.include/fault/metrics.h will call the original main after
		// noting the execution in the (system/envvar)`FAULT_CAPTURE_DIRECTORY` directory.
	*/
	#define FAULT_EXECUTABLE(name) _fault_application_##name
	#define fmain _fault_application_main

	#include <fault/metrics.h>
#endif
