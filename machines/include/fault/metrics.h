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
	static void __attribute__((destructor))
	_fault_llvm_telemetry_dispatch(void)
	{
		static char ifbuf[4096];
		char pibuf[32];
		const char *mcp = getenv("METRICS_CAPTURE");
		const char *pid = getenv("PROCESS_IDENTITY");
		const char *mid = getenv("METRICS_IDENTITY");

		/* METRICS_CAPTURE or the compile time default. */
		if (mcp == NULL)
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
		if (pid == NULL)
		{
			pid = pibuf;
			snprintf(pibuf, sizeof(pibuf), "%ld", (long) getpid());
		}

		/* METRICS_IDENTITY or the constant. */
		if (mid == NULL)
			mid = ".fault-llvm";

		snprintf(ifbuf, sizeof(ifbuf),
			"%s/%s/%s/.llvm.profraw",
			mcp, pid, mid
		);

		fs_alloc(0, ifbuf, S_IRWXU|S_IRWXG|S_IRWXO);
		__llvm_profile_set_filename(ifbuf);
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
