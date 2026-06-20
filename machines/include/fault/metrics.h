/**
	// Telemetry control for factors built with metrics captures.

	// [ Integration Control Defines ]
	// /FAULT_METRICS_LINKED/
		// Define used to signal that the telemetry will be written by another
		// factor and that only a link should be created when the captured
		// data is transmitted.
*/

/*
	// fault-metrics LLVM profile support.
*/
#if defined(F_LLVM_INSTRUMENTATION) && defined(F_TELEMETRY)
	#include <stdio.h>
	#include <stdlib.h>
	#include <stdint.h>
	#include <inttypes.h>
	#include <sys/types.h>
	#include <unistd.h>
	#include <string.h>
	#include <spawn.h>
	#include <sys/wait.h>
	#include <errno.h>
	#include <fcntl.h>
	#include <pthread.h>
	#include <sys/sysctl.h>
	#include <fault/fs.h>
	#include <fault/symbols.h>

	void __llvm_profile_write_file(void);
	void __llvm_profile_reset_counters(void);
	void __llvm_profile_set_filename(const char *);
	void __llvm_profile_initialize_file(void);

	// Link stack for creating links to the captured data.
	struct _factor_metrics_chain {
		void (*update)(const char *);
		struct _factor_metrics_chain *next;
	};

	static char _factor_metrics_isolation[512];
	static char _fault_lcounters[4096 * 2];
	#ifndef FAULT_METRICS_LINKED
		static char _fault_llvm_imd[4096 * 2];
		static char _fault_llvm_imr[4096 * 2];
		struct _factor_metrics_chain * CONCEAL(_factor_metrics_link_stack) = NULL;
		const char * CONCEAL(_factor_metrics_primary) = FACTOR_PATH_STR;
	#else
		extern struct _factor_metrics_chain *_factor_metrics_link_stack;
		extern const char *_factor_metrics_primary;
	#endif

	/**
		// Update the filesystem locations used to transmit the captured metrics.
	*/
	static void
	_factor_metrics_update_telemetry(void)
	{
		#define _f_empty_string(X) (X == NULL || strlen(X) == 0)
		int ifbuflen;
		char pibuf[6 + (5 * (sizeof(intmax_t) / 2))];
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
			pid_t curpid = getpid();
			pid = pibuf;
			#define _PID_FMT(P) \
				_Generic(P, int32_t: "%" PRId32, uint32_t: "%" PRIu32, uintmax_t: "%" PRIuMAX, default: "%" PRIdMAX)
			#define _PID_CAST(P) \
				_Generic(P, int32_t: P, uint32_t: P, uintmax_t: P, default: (intmax_t) P)
			snprintf(pibuf, sizeof(pibuf), _PID_FMT(curpid), _PID_CAST(curpid));
			#undef _PID_FMT
			#undef _PID_CAST
		}

		if (_f_empty_string(mid))
		{
			// METRICS_IDENTITY; usually the test identity.

			// The dot-prefix here is significant as it will cause aggregate
			// to pass over the data. Test runners are expected to set this
			// to the factor and element path with telemetry_identify.
			mid = ".fault-llvm";
		}

		if (_f_empty_string(mi))
		{
			// METRICS_ISOLATION; the environment's custom grouping for data.
			mi = "unspecified";
		}

		// Copy for the conversion (destructor) function.
		snprintf(_factor_metrics_isolation, sizeof(_factor_metrics_isolation),
			"%s", mi
		);

		#ifndef FAULT_METRICS_LINKED
			snprintf(_fault_lcounters, sizeof(_fault_lcounters),
				"%s/%s/%s/.fault-syntax-counters/l-counters",
				mcp, pid, mid
			);
		#else
			/*
				// When linking to the primary factor's l-counters,
				// the linked factor needs to be qualified by the primary
				// in order to avoid losing information. In cases where
				// multiple DSO's are present, the collected metrics will be
				// written to multiple locations. If the linked factor is
				// used by more than one DSO and unqualified, the first link
				// will be the only link.
			*/
			snprintf(_fault_lcounters, sizeof(_fault_lcounters),
				"%s/%s:%s/%s/.fault-syntax-counters/l-counters",
				mcp, pid, _factor_metrics_primary, mid
			);
		#endif

		// Allocate directories for l-counters and LLVM data files.
		fs_alloc(fs_mkdir_defaults, _fault_lcounters, S_IRWXU|S_IRWXG|S_IRWXO);

		#ifndef FAULT_METRICS_LINKED
			snprintf(_fault_llvm_imr, sizeof(_fault_llvm_imr),
				"%s/%s/%s/.fault-llvm-counters/%s.raw",
				mcp, pid, mid, mi
			);
			snprintf(_fault_llvm_imd, sizeof(_fault_llvm_imd),
				"%s/%s/%s/.fault-llvm-counters/%s.merged",
				mcp, pid, mid, mi
			);
			fs_alloc(fs_mkdir_defaults, _fault_llvm_imr, S_IRWXU|S_IRWXG|S_IRWXO);
			__llvm_profile_set_filename(_fault_llvm_imr);
		#endif
		#undef _f_empty_string
	}

	#ifndef FAULT_METRICS_LINKED
		static void
		_factor_metrics_identify(const char *)
		{
			_factor_metrics_update_telemetry();

			for (struct _factor_metrics_chain *ls = _factor_metrics_link_stack; ls != NULL; ls = ls->next)
				ls->update(_fault_lcounters);
		}

		static void
		_fault_llvm_metrics_convert(void)
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
			dprintf(fd, "%s&%s\n", lseek(fd, 0, SEEK_END) ? "\n" : "", _factor_metrics_isolation);

			// Extract counters from the merged data.
			posix_spawn_file_actions_init(&fa);
			posix_spawn_file_actions_adddup2(&fa, fd, STDOUT_FILENO);
			posix_spawn(&pid, imq_argv[0], &fa, NULL, imq_argv, NULL);
			posix_spawn_file_actions_destroy(&fa);
			waitpid(pid, &status, 0);
		}

		// Executed (destructor) after LLVM performs its default &__llvm_profile_write_file.
		static void __attribute__((destructor))
		_factor_metrics_commit(void)
		{
			// Run merge and ipq appending to l-counters.
			_fault_llvm_metrics_convert();
		}

		static void
		_factor_metrics_transmit(void)
		{
			__llvm_profile_write_file();
			__llvm_profile_reset_counters();
			_factor_metrics_commit();
		}

		struct telemetry_controls {
			void (*identify)(const char *);
			void (*transmit)(void);
			void (*discard)(void);
			void (*enable)(void);
			void (*disable)(void);

			struct telemetry_controls *next;
		};

		struct telemetry_controls _factor_metrics_controls = {
			_factor_metrics_identify,
			_factor_metrics_transmit,
			__llvm_profile_reset_counters,
			NULL,
		};

		// Optional. Usually provided by the executable.
		void telemetry_register(struct telemetry_controls *) __attribute__((weak));

		static void
		_factor_metrics_update_identity(void)
		{
			_factor_metrics_identify(NULL);
		}

		static void __attribute__((constructor(999)))
		_factor_metrics_initialize(void)
		{
			// Register with telemetry if available.
			if (telemetry_register != NULL)
				telemetry_register(&_factor_metrics_controls);

			_factor_metrics_update_telemetry();
			pthread_atfork(NULL, NULL, _factor_metrics_update_identity);
		}
	#else
		static void
		_factor_metrics_link_identify(const char *primary)
		{
			_factor_metrics_update_telemetry();
			symlink(primary, _fault_lcounters);
		}

		static void __attribute__((constructor(900)))
		_factor_metrics_link_chain(void)
		{
			static struct _factor_metrics_chain link;
			link.next = _factor_metrics_link_stack;
			link.update = _factor_metrics_link_identify;
			_factor_metrics_link_stack = &link;
		}
	#endif
#endif
