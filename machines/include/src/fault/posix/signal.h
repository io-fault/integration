/**
	// Signal table macros providing categorized signal names.
	// The defined list macros provide the means to construct mappings between
	// the signal code, identifier(POSIX macro names), category, and name.
	// Where the signal category and signal name are the locally contrived properties.

	// (system/signal)`SIGSTOP` and (system/signal)`SIGKILL` are not included in
	// &SIGNAL_LIST as they cannot normally be trapped. When expanding the complete
	// list for mappings, &UNTRAPPABLE_SIGNAL_LIST should also be referenced.

	// Usage:

	// #!syntax/c
		#define SIG(N, C, I) \
			case SIG##N: return(#C "/" #I); break;
		switch (signo)
		{
			SIGNAL_LIST()
			UNTRAPPABLE_SIGNAL_LIST()
		}
		#undef SIG
*/
#ifndef _FAULT_POSIX_SIGNAL_H_included_
#define _FAULT_POSIX_SIGNAL_H_included_

#define PROCESS_SIGNAL_LIST() \
	SIG(TSTP, process, suspend) \
	SIG(CONT, process, continue) \
	SIG(ABRT, process, abort) \
	SIG(TERM, process, terminate) \
	SIG(INT, process, interrupt) \
	SIG(QUIT, process, quit)

#define LIMIT_SIGNAL_LIST() \
	SIG(XCPU, limit, cpu) \
	SIG(XFSZ, limit, file) \
	SIG(ALRM, limit, time) \
	SIG(PROF, limit, profiling) \
	SIG(VTALRM, limit, virtual)

#define TERMINAL_SIGNAL_LIST() \
	SIG(HUP, terminal, closed) \
	SIG(INFO, terminal, query) \
	SIG(TTIN, terminal, background-read) \
	SIG(TTOU, terminal, background-write) \
	SIG(WINCH, terminal, delta)

#define EVENT_SIGNAL_LIST() \
	SIG(CHLD, event, child-status) \
	SIG(IO, event, io) \
	SIG(URG, event, urgent-condition) \
	SIG(TRAP, event, trap) \
	SIG(USR1, event, user-1) \
	SIG(USR2, event, user-2)

#define EXCEPTION_SIGNAL_LIST() \
	SIG(FPE, exception, floating-point) \
	SIG(PIPE, exception, broken-pipe)

#define ERROR_SIGNAL_LIST() \
	SIG(SEGV, error, restricted-memory-access) \
	SIG(BUS, error, invalid-memory-access) \
	SIG(ILL, error, invalid-instruction) \
	SIG(SYS, error, invalid-system-call)

#define UNTRAPPABLE_SIGNAL_LIST() \
	SIG(STOP, process, stop) \
	SIG(KILL, process, kill)

#define SIGNAL_LIST() \
	PROCESS_SIGNAL_LIST() \
	LIMIT_SIGNAL_LIST() \
	TERMINAL_SIGNAL_LIST() \
	EVENT_SIGNAL_LIST() \
	EXCEPTION_SIGNAL_LIST() \
	ERROR_SIGNAL_LIST()
#endif
