/**
	// Control telemetry locations for supported instrumentation frameworks.
*/

/**
	// fault-metrics LLVM profile support.
*/
#if defined(F_LLVM_INSTRUMENTATION) && defined(F_TELEMETRY)
	#include <fault/fs.h>
	void __llvm_profile_write_file(void);
	void __llvm_profile_reset_counters(void);
	void __llvm_profile_set_filename(const char *);
	void __llvm_profile_initialize_file(void);

	/**
		// Assign the target profdata file.
		// Performed atexit, registered by _fault_llvm_telemetry_register.
	*/
	static void __attribute__((constructor))
	_fault_llvm_telemetry_dispatch(void)
	{
		#define _f_empty_string(X) (X == NULL || strlen(X) == 0)
		static char ifbuf[4096];
		char pibuf[32];
		const char *mcp = getenv("METRICS_CAPTURE");
		const char *pid = getenv("PROCESS_IDENTITY");
		const char *mid = getenv("METRICS_IDENTITY");
		const char *mi = getenv("METRICS_ISOLATION");

		/* METRICS_CAPTURE or the compile time default. */
		if (_f_empty_string(mcp))
		{
			#if defined(IF_coverage)
				mcp = F_TELEMETRY "/coverage";
			#elif defined(IF_profile)
				mcp = F_TELEMETRY "/profile";
			#else
				mcp = F_TELEMETRY "/unclassified";
			#endif
		}

		/* PROCESS_IDENTITY or the string representation of getpid() */
		if (_f_empty_string(pid))
		{
			pid = pibuf;
			snprintf(pibuf, sizeof(pibuf), "%ld", (long) getpid());
		}

		/* METRICS_IDENTITY or the constant. */
		if (_f_empty_string(mid))
			mid = ".fault-llvm";

		/* METRICS_ISOLATION */
		if (_f_empty_string(mi))
			mi = "unspecified";

		snprintf(ifbuf, sizeof(ifbuf),
			"%s/%s/%s/%s",
			mcp, pid, mid, mi
		);

		fs_alloc(0, ifbuf, S_IRWXU|S_IRWXG|S_IRWXO);
		__llvm_profile_set_filename(ifbuf);
		#undef _f_empty_string
	}

	#if 0
	static void __attribute__((constructor))
	_fault_llvm_telemetry_register(void)
	{
		/* Defer file assignment in case of environment changes. */
		atexit(_fault_llvm_telemetry_dispatch);
	}
	#endif
#endif
