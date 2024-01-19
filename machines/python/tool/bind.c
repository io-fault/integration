/**
	// Factor execution tool.
*/
#include <fault/python/bind.h>
#define TARGET_MODULE "fault.system.tool"
#define FAULT_PYTHON_CONTROL_IMPORTS \
	IMPORT("fault.context.execute") \
	IMPORT("system.context.execute")
#include <fault/python/execute.h>
