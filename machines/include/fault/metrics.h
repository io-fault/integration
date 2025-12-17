/**
	// Control telemetry locations for supported instrumentation frameworks.
*/

/**
	// fault-metrics LLVM profile support.
*/
#if defined(F_LLVM_INSTRUMENTATION) && defined(F_TELEMETRY)
	#include <stdio.h>
	#include <stdlib.h>
	#include <sys/types.h>
	#include <unistd.h>
	#include <string.h>
	#include <spawn.h>
	#include <sys/wait.h>
	#include <errno.h>
	#include <fcntl.h>
	#include <pthread.h>
	#include <fault/fs.h>
	#include <sys/sysctl.h>

	void __llvm_profile_write_file(void);
	void __llvm_profile_reset_counters(void);
	void __llvm_profile_set_filename(const char *);
	void __llvm_profile_initialize_file(void);
	static char _fault_llvm_imd[4096 * 2];
	static char _fault_llvm_imr[4096 * 2];
	static char _fault_lcounters[4096 * 2];
	static char _fault_metrics_isolation[512];

	/**
		// Assign the target profdata file.
		// Performed atexit, registered by _fault_llvm_telemetry_register.
	*/
	static void
	_fault_update_telemetry(void)
	{
		#define _f_empty_string(X) (X == NULL || strlen(X) == 0)
		int ifbuflen;
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

		if (_f_empty_string(pid))
		{
			// PROCESS_IDENTITY; usually drawn from the actual PID.
			pid = pibuf;
			snprintf(pibuf, sizeof(pibuf), "%ld", (long) getpid());
		}

		if (_f_empty_string(mid))
		{
			// METRICS_IDENTITY; usually the test identity.

			// The dot-prefix here is significant as it will cause aggregate
			// to pass over the data. Test runners are expected to set this
			// to the factor and element path.
			mid = ".fault-llvm";
		}

		if (_f_empty_string(mi))
		{
			// METRICS_ISOLATION; the environment's custom grouping for data.
			mi = "unspecified";
		}

		// Copy for the conversion (destructor) function.
		snprintf(_fault_metrics_isolation, sizeof(_fault_metrics_isolation),
			"%s", mi
		);
		snprintf(_fault_llvm_imr, sizeof(_fault_llvm_imr),
			"%s/%s/%s/.fault-llvm-counters/%s.raw",
			mcp, pid, mid, mi
		);
		snprintf(_fault_llvm_imd, sizeof(_fault_llvm_imd),
			"%s/%s/%s/.fault-llvm-counters/%s.merged",
			mcp, pid, mid, mi
		);
		snprintf(_fault_lcounters, sizeof(_fault_lcounters),
			"%s/%s/%s/.fault-syntax-counters/l-counters",
			mcp, pid, mid
		);

		// Allocate directories for l-counters and LLVM data files.
		fs_alloc(0, _fault_lcounters, S_IRWXU|S_IRWXG|S_IRWXO);
		fs_alloc(0, _fault_llvm_imr, S_IRWXU|S_IRWXG|S_IRWXO);

		__llvm_profile_set_filename(_fault_llvm_imr);
		#undef _f_empty_string
	}

	static void __attribute__((constructor))
	_fault_llvm_telemetry_init(void)
	{
		_fault_update_telemetry();
		pthread_atfork(NULL, NULL, _fault_update_telemetry);
	}

	static void __attribute__((destructor))
	_fault_llvm_telemetry_convert(void)
	{
		pid_t pid = 0;
		int fd = -1, status = -1;
		posix_spawn_file_actions_t fa;

		char *lpd_argv[] = {
			CC_PATH "/.llvm/pd-tool", "merge",
			"-o", _fault_llvm_imd,
			_fault_llvm_imr, NULL
		};
		char *imq_argv[] = {
			CC_PATH "/.llvm/clang-ipq", "counters",
			F_FACTOR_IMAGE,
			_fault_llvm_imd, NULL
		};

		// No llvm-profdata executable.
		if (access(lpd_argv[0], X_OK) != 0)
			return;

		// No ipquery executable.
		if (access(imq_argv[0], X_OK) != 0)
			return;

		// Try writing. (earlier version of LLVM presumably)
		if (access(_fault_llvm_imr, F_OK) != 0)
			__llvm_profile_write_file();

		if (access(_fault_llvm_imr, F_OK) != 0)
		{
			// No data to process.
			return;
		}

		// Merge the raw data so that it can be read.
		posix_spawn_file_actions_init(&fa);
		posix_spawn_file_actions_adddup2(&fa, STDERR_FILENO, STDOUT_FILENO);
		posix_spawn(&pid, lpd_argv[0], &fa, NULL, lpd_argv, NULL);
		posix_spawn_file_actions_destroy(&fa);
		waitpid(pid, &status, 0);

		// Prepare l-counters, and switch the metrics isolation.
		fd = open(_fault_lcounters, O_WRONLY|O_CREAT|O_APPEND, S_IRUSR|S_IWUSR);
		dprintf(fd, "&%s\n", _fault_metrics_isolation);

		// Extract counters from the merged data.
		posix_spawn_file_actions_init(&fa);
		posix_spawn_file_actions_adddup2(&fa, fd, STDOUT_FILENO);
		posix_spawn(&pid, imq_argv[0], &fa, NULL, imq_argv, NULL);
		posix_spawn_file_actions_destroy(&fa);
		waitpid(pid, &status, 0);
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
