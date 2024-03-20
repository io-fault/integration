#ifndef FAULT_SUPPRESS_CONTEXT
	#ifdef __APPLE__
		#include <TargetConditionals.h>
	#endif

	#if FAULT_PYTHON_IMPLEMENTATION == 1
		#include <fault/python/implementation/Python.h>
		#include <fault/python/implementation/marshal.h>
	#else
		#include <Python.h>
		#include <marshal.h>
	#endif

	#include <unistd.h>
	#include <signal.h>

	#ifdef __FreeBSD__
		#include <fenv.h>
	#endif

	#ifndef FAULT_CONTEXT_NAME
		#define FAULT_CONTEXT_NAME "fault"
	#endif

	#if PY_VERSION_HEX < 0x03050000
		/* Renamed in 3.5+ */
		#define Py_DecodeLocale _Py_char2wchar
	#endif

	#include <fault/libc.h>
#endif

/**
	// Identify the initialization method to employ.

	// Version 1 being nearly bitrot with the changes to
	// tool bindings using the &system.root.python generated
	// header.
*/
#if !defined(PYTHON_INITIALIZATION_VERSION)
	#if PY_MAJOR_VERSION >= 3 && PY_MINOR_VERSION >= 8
		/* PyPreConfig and PyConfig */
		#define PYTHON_INITIALIZATION_VERSION 2
	#else
		/* Py_* globals and Py_Initialize */
		#define PYTHON_INITIALIZATION_VERSION 1
		#ifndef PYTHON_PATH
			#error PYTHON_PATH must be supplied with versions before 3.8
		#endif
	#endif
#elif PYTHON_INTIALIZATION_VERSION == 1
	/*
		// Disable version 1 and warn if Python >= 3.12.
	*/
	#if PY_MAJOR_VERSION >= 3 && PY_MINOR_VERSION >= 12
		#warning Defined PYTHON_INITIALIZATION_VERSION uses deprecated APIs in 3.12
		#warning Using v2 relying on PyConfig APIs.

		#undef PYTHON_INITIALIZATION_VERSION
		#define PYTHON_INITIALIZATION_VERSION 2
	#endif
#endif

/**
	// Defines controlling the exit procedure after encountering errors.

	// For single execution cases, exiting with signal status (panic) is consistent with return.
	// However, in embedding contexts, it is likely that the controlling environment
	// needs to continue and may even be able to correct the issue.
*/
#ifndef EX_INIT
	#define EX_INIT 254
#endif

#ifdef EX_PANIC
	#define panic() do {signal(SIGUSR2, SIG_DFL); kill(getpid(), SIGUSR2);} while(0)
#else
	#define panic() do {} while(0)
#endif

/**
	// Rename the main symbol for isolated environments.
	// `#define main ...` would work as well, but avoid the risk
	// of unwanted substitutions with an explicit and longer name.
*/
#ifndef SYSTEM_ENTRY_POINT
	#define SYSTEM_ENTRY_POINT main
#endif

#ifndef DEFAULT_ENTRY_POINT
	/*
		// The attribute on TARGET_MODULE to execute.
	*/
	#define DEFAULT_ENTRY_POINT "main"
#endif

#define _PREFIX(X,STRING) X##STRING
#define LSTR(STRING) _PREFIX(L,STRING)
#define log(category, message, ...) \
	fprintf(stderr, "[!* " category ": " message "]\n", ##__VA_ARGS__)

#ifndef CONTROL_ACTIVATION_SYMBOL
	#define CONTROL_ACTIVATION_SYMBOL "activate"
#endif

#ifndef FACTOR_SYSTEM
	#define FACTOR_SYSTEM FV_SYSTEM_STR
#endif

#ifndef FACTOR_ARCHITECTURE
	#define FACTOR_ARCHITECTURE FV_ARCHITECTURE_STR
#endif

#ifndef FACTOR_PYTHON
	#define FACTOR_PYTHON "cpython" \
		STRING_FROM_IDENTIFIER(PY_MAJOR_VERSION) \
		STRING_FROM_IDENTIFIER(PY_MINOR_VERSION)
#endif

#ifndef ARGUMENTS
	#define ARGUMENT_COUNT 0
	#define ARGUMENTS
#endif

#ifndef EXECUTION_FACTOR_PATH
	#define EXECUTION_FACTOR_PATH_STR F_PRODUCT_PATH
	#define EXECUTION_FACTOR_PATH \
		FACTOR_PATH_STRING(F_PRODUCT_PATH)
#endif

#ifndef FACTOR_IMAGES
	#define FACTOR_IMAGES ".images"
#endif

#ifndef FACTOR_INTENTION
	#define FACTOR_INTENTION "optimal"
#endif

#ifndef FAULT_INTENTION
	#define FAULT_INTENTION "optimal"
#endif

#define FAULT_CONTEXT_PATH FAULT_PYTHON_PRODUCT "/" FAULT_CONTEXT_NAME
#define FAULT_SYSTEM_PATH FAULT_CONTEXT_PATH "/system"
#define PYTHON_IMAGES FACTOR_SYSTEM "-" FACTOR_PYTHON

#ifndef FAULT_BOOTSTRAP_SOURCE
	#define FAULT_BOOTSTRAP_SOURCE \
		(FAULT_SYSTEM_PATH "/bootstrap.py")
#endif

#ifndef FAULT_BOOTSTRAP_BYTECODE
	#define FAULT_BOOTSTRAP_BYTECODE \
		(FAULT_PYTHON_PRODUCT "/" FACTOR_IMAGES "/" PYTHON_IMAGES \
		"/" FAULT_CONTEXT_NAME "/" "system" "/" \
		"bootstrap.i")
#endif

/**
	// Create a &fault.system.process.Invocation instance from the system process.
	// Used by bindings calling explicit entry points.
*/
static PyObject *
fault_system_invocation(PyObject **process_module)
{
	PyObject *mod, *ic, *inv;

	mod = PyImport_ImportModule(FAULT_CONTEXT_NAME ".system.process");
	if (mod == NULL)
		return(NULL);

	ic = PyObject_GetAttrString(mod, "Invocation");
	if (ic == NULL)
	{
		Py_DECREF(mod);
		return(NULL);
	}

	/* Construct Invocation instance using (Python) system provided arguments */
	inv = PyObject_CallMethod(ic, "system", "");
	Py_DECREF(ic);
	if (inv == NULL)
		Py_DECREF(mod);

	*process_module = mod;
	return(inv);
}
/**
	// Execute the bytecode or source for bootstrapping the factor loader.
*/
static PyObject *
fault_python_bootstrap(const char *bytecode, const char *source)
{
	FILE *fp;
	PyObject *code, *r, *module, *exedict;

	module = PyModule_New("__bootstrap__");
	if (module == NULL)
		return(NULL);
	exedict = PyModule_GetDict(module);

	if (PyModule_AddStringConstant(module, "__file__", source) != 0)
	{
		Py_DECREF(module);
		return(NULL);
	}

	if (bytecode != NULL)
	{
		if (PyModule_AddStringConstant(module, "__cache__", bytecode) != 0)
		{
			Py_DECREF(module);
			return(NULL);
		}

		fp = fopen(bytecode, "rb");
		if (fp != NULL)
		{
			code = PyMarshal_ReadObjectFromFile(fp);
			fclose(fp);

			if (code != NULL)
			{
				r = PyEval_EvalCode(code, exedict, exedict);
				Py_DECREF(code);

				if (r != NULL)
				{
					/* Succesfully bootstrapped */
					Py_DECREF(r);
					return(module);
				}

				/* Fallback on source. */
				PyErr_Clear();
			}
		}
	}

	fp = fopen(source, "rb");
	if (fp == NULL)
	{
		/* Source could not be opened */
		Py_DECREF(module);
		return(NULL);
	}

	r = PyRun_File(fp, source, Py_file_input, exedict, exedict);
	fclose(fp);
	fp = NULL;

	if (r != NULL)
	{
		Py_DECREF(r);
		return(module);
	}

	/* Source execution failed. */
	Py_DECREF(module);
	return(NULL);
}

/**
	// Allocate and convert system arguments for loading sys.argv as bin/python would.
*/
static wchar_t **
aalloc(int argc, char *argv[])
{
	int i, r = 0;
	size_t nbytes;
	wchar_t **wargv;

	nbytes = sizeof(wchar_t *) * (argc + 1 + ARGUMENT_COUNT);
	wargv = PyMem_RawMalloc(nbytes);
	if (wargv == NULL)
	{
		log("ERROR", "could not allocate %zd bytes of memory for system arguments", nbytes);
		return(NULL);
	}

	i = 0;
	#define ARGUMENT(ARGSTR) \
		wargv[i] = Py_DecodeLocale(ARGSTR, NULL); \
		if (wargv[i] == NULL) \
		{ \
			log("ERROR", "could not decode system arguments for application"); \
			return(NULL); \
		} \
		++i;

		/* Constants first then actual arguments */
		ARGUMENT(argv[0]);
		ARGUMENTS
		for (r = 1; r < argc; ++r)
		{
			ARGUMENT(argv[r]);
		}
	#undef ARGUMENT

	return(wargv);
}

#if PYTHON_INITIALIZATION_VERSION == 1
static int
fault_python_initialize(int argc, char **argv)
{
	int r;
	wchar_t **wargv;
	PyObject *ob;

	/**
		// The python.org binary conditionally runs this on FreeBSD.
		// Arguably, it should be a no-op on any platform if it's already off.
	*/
	#ifdef __FreeBSD__
		fedisableexcept(FE_OVERFLOW);
	#endif

	Py_NoUserSiteDirectory = 1;
	Py_IgnoreEnvironmentFlag = 1;
	Py_DebugFlag = 0;
	Py_BytesWarningFlag = 2;
	Py_IsolatedFlag = 1;
	Py_DontWriteBytecodeFlag = 1;

	wargv = aalloc(argc, argv);
	if (wargv == NULL)
	{
		panic();
		return(EX_INIT);
	}

	/*
		// sys.executable explicitly configured by the binding.
		// Normally this should point to the Python executable within the installation prefix.
	*/
	Py_SetProgramName(LSTR(PYTHON_EXECUTABLE_PATH));

	#ifdef PYTHON_PATH
		/*
			// Hardcoded at compile time. Relocating/removing the dependency requires
			// the executable to be rebuilt.
		*/
		Py_SetPath(LSTR(PYTHON_PATH_STR));
	#endif

	Py_Initialize();
	if (!Py_IsInitialized())
	{
		log("ERROR", "could not initialize python runtime");
		panic();
		return(EX_INIT);
	}

	PySys_SetArgvEx(argc + ARGUMENT_COUNT, wargv, 0);

	#if (PY_MAJOR_VERSION == 3 && PY_MINOR_VERSION < 7) || PY_MAJOR_VERSION < 3
	{
		/* No-op in 3.7 and greater. */
		PyEval_InitThreads();
		if (!PyEval_ThreadsInitialized())
		{
			log("ERROR", "could not initialize threading");
			panic();
			return(EX_INIT);
		}
	}
	#endif

	/* Check the success of the prior Py_SetPath */
	ob = PySys_GetObject("path");
	if (ob == NULL)
	{
		log("ERROR", "could not initialize execution context");
		panic();
		return(EX_INIT);
	}
}
#endif

#if PYTHON_INITIALIZATION_VERSION == 2
static int
fault_python_initialize(int argc, char **argv)
{
	int r;
	wchar_t **wargv;
	PyStatus status;
	PyPreConfig precfg;
	PyConfig cfg;

	wargv = aalloc(argc, argv);
	if (wargv == NULL)
	{
		panic();
		return(EX_INIT);
	}

	PyPreConfig_InitIsolatedConfig(&precfg);
	precfg.utf8_mode = 1;
	precfg.parse_argv = 0;

	status = Py_PreInitialize(&precfg);
	if (PyStatus_IsError(status))
		goto initerror;

	PyConfig_InitIsolatedConfig(&cfg);

	cfg.pathconfig_warnings = 0;
	cfg.use_environment = 0;
	cfg.bytes_warning = 0;
	cfg.configure_c_stdio = 1;
	cfg.install_signal_handlers = 0;
	cfg.interactive = 0;
	cfg.isolated = 1;
	cfg.optimization_level = 2;
	cfg.site_import = 0;
	cfg.user_site_directory = 0;
	cfg.write_bytecode = 0;
	cfg.quiet = 1;
	cfg.module_search_paths_set = 0;

	#ifdef PYTHON_EXECUTABLE_PATH
		status = PyConfig_SetString(&cfg, &cfg.base_executable, LSTR(PYTHON_EXECUTABLE_PATH));
		if (PyStatus_IsError(status))
			goto initerror;
	#endif

	status = PyConfig_SetArgv(&cfg, argc + ARGUMENT_COUNT, wargv);
	if (PyStatus_IsError(status))
		goto initerror;

	status = Py_InitializeFromConfig(&cfg);
	if (PyStatus_IsError(status))
		goto initerror;

	goto finish;

	initerror:
	{
		log("ERROR", "could not initialize execution context");
		fprintf(stderr, "%s: %s\n", status.func ? status.func : "", status.err_msg);
		panic();
		PyConfig_Clear(&cfg);
		fflush(stderr);
		return(EX_INIT);
	}

	finish:
	{
		PyConfig_Clear(&cfg);
	}

	return(0);
}
#endif

static int
fault_python_bootstrap_factors()
{
	PyObject *boots, *factors;

	boots = fault_python_bootstrap(FAULT_BOOTSTRAP_BYTECODE, FAULT_BOOTSTRAP_SOURCE);
	if (boots == NULL)
	{
		log("ERROR", "could not bootstrap the factor loader");
		PyErr_Print();
		PyErr_Clear();
		fflush(stderr);
		panic();
		return(EX_INIT);
	}

	/* Product paths given as varargs. */
	factors = PyObject_CallMethod(boots, "integrate",
		#define FACTOR_PATH_STRING(x) "s"
			"ssssssss"
			EXECUTION_FACTOR_PATH,
		#undef FACTOR_PATH_STRING

		FAULT_PYTHON_PRODUCT,
		FAULT_CONTEXT_NAME,
		FAULT_INTENTION,
		FACTOR_IMAGES,
		FACTOR_SYSTEM,
		FACTOR_PYTHON,
		FACTOR_ARCHITECTURE,
		FACTOR_INTENTION

		#define FACTOR_PATH_STRING(x) , x
			EXECUTION_FACTOR_PATH
		#undef FACTOR_PATH_STRING
	);
	Py_DECREF(boots);

	if (factors == NULL)
	{
		log("ERROR", "could not bootstrap the factor loader");
		PyErr_Print();
		PyErr_Clear();
		fflush(stderr);
		panic();
		return(EX_INIT);
	}

	Py_DECREF(factors);
	return(0);
}

static int
fault_python_import_controls(const char *module_name, const char *attribute)
{
	PyObject *init_exit_object = NULL;
	PyObject *control_module = NULL;

	#ifdef FAULT_PYTHON_CONTROL_IMPORTS
		#define IMPORT(x) \
			control_module = PyImport_ImportModule(x); \
			if (control_module == NULL) { \
				log("ERROR", "could not import control module"); \
				PyErr_Print(); \
				fflush(stderr); \
				panic(); \
				return(EX_INIT); \
			} \
			init_exit_object = PyObject_CallMethod(control_module, \
				CONTROL_ACTIVATION_SYMBOL, "ss", module_name, attribute); \
			Py_DECREF(control_module); \
			if (init_exit_object == NULL) { \
				log("ERROR", "control module (%s) activation raised exception", x); \
				PyErr_Print(); \
				fflush(stderr); \
				panic(); \
				return(EX_INIT); \
			} \
			else \
				Py_DECREF(init_exit_object);

			FAULT_PYTHON_CONTROL_IMPORTS;
		#undef IMPORT
	#endif

	return(0);
}

static PyObject *
fault_python_execute(const char *module_name, const char *attribute)
{
	PyObject *ob, *mod = NULL;
	PyObject *_f_process = NULL;
	PyObject *_f_sysinv = NULL;
	PyObject *_f_main = NULL;

	/*
		// Inherit compile time default if unspecified.
	*/
	mod = PyImport_ImportModule(module_name);
	if (mod == NULL)
	{
		log("ERROR", "could not import application module: %s", module_name);
		goto error;
	}

	/**
		// Main execution. Calls DEFAULT_ENTRY_POINT in TARGET_MODULE.
		// For fault invocations, a &fault.system.process.Invocation instance
		// is created and passed to main.
	*/

	_f_main = PyObject_GetAttrString(mod, attribute);
	if (_f_main == NULL)
	{
		log("ERROR", "could not get entry point from "
			"application module: %s", attribute);
		goto error;
	}
	_f_sysinv = fault_system_invocation(&_f_process);

	if (_f_sysinv == NULL)
	{
		log("ERROR", "could not create Invocation instance");
		goto error;
	}
	ob = PyObject_CallMethod(_f_process, "control", "OO", _f_main, _f_sysinv);

	Py_DECREF(_f_process);
	Py_DECREF(_f_main);
	Py_DECREF(_f_sysinv);
	Py_DECREF(mod);

	/* Error case handled by caller. */
	return(ob);

	error:
	{
		/* Print and Clear so fault_python_exit_status doesn't print again. */
		PyErr_Print();
		PyErr_Clear();

		Py_XDECREF(mod);
		Py_XDECREF(_f_main);
		Py_XDECREF(_f_sysinv);
		Py_XDECREF(_f_process);

		panic();
		return(NULL);
	}
}

static int
fault_python_exit_status(PyObject *exit_status)
{
	int r = 255;

	if (exit_status != NULL)
	{
		/*
			// As an alternative, entry points may choose to return
			// the exit status directly. However, SystemExit is supported as well.
		*/

		if (exit_status == Py_None)
		{
			r = 0;
		}
		else if (PyLong_Check(exit_status))
		{
			r = (int) PyLong_AsLong(exit_status);
		}

		Py_DECREF(exit_status);
		exit_status = NULL;
	}
	else if (PyErr_Occurred())
	{
		/* Capture exit code from raise SystemExit */
		if (PyErr_ExceptionMatches(PyExc_SystemExit))
		{
			PyObject *exc, *val, *tb;
			PyErr_Fetch(&exc, &val, &tb);
			PyObject *pi;

			if (val)
			{
				pi = PyObject_GetAttrString(val, "code");
				if (pi)
				{
					r = (int) PyLong_AsLong(pi);
					Py_DECREF(pi);
				}
			}

			Py_DECREF(exc);
			Py_XDECREF(val);
			Py_XDECREF(tb);

			PyErr_Clear();
		}
		else
		{
			log("ERROR", "application raised exception");
			PyErr_Print();
			PyErr_Clear();
			fflush(stderr);
		}
	}
	else
	{
		/* Initialization error status already reported. */
		r = EX_INIT;
	}

	return(r);
}

static void
fault_python_close()
{
	Py_Finalize();
}

int
SYSTEM_ENTRY_POINT(int argc, char *argv[])
{
	int r = 255;
	PyObject *rob;

	r = fault_python_initialize(argc, argv);
	if (r != 0)
		return(r);

	/* fault.system.factors loader */
	r = fault_python_bootstrap_factors();
	if (r != 0)
		goto exit;

	/* Pre-import initialization. */
	r = fault_python_import_controls(TARGET_MODULE, DEFAULT_ENTRY_POINT);
	if (r != 0)
		goto exit;

	rob = fault_python_execute(TARGET_MODULE, DEFAULT_ENTRY_POINT);
	r = fault_python_exit_status(rob); /* Releases &ob */

	exit:
	{
		fault_python_close();
	}

	return(r);
}
