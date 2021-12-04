/**
	// Signal table macro providing categorized signal identifiers
	// and protection against missing signal defines for commonly
	// used signals.
*/
#ifndef _FAULT_POSIX_SIGNAL_H_included_
#define _FAULT_POSIX_SIGNAL_H_included_

/**
	// Contrived signal for maintaining invariants
*/
#define SIGNEVER -1

/**
	// Macro providing a list of common signals with
	// a categorized abstract title.
*/
#define FAULT_SIGNAL_LIST() \
	SIG(CHLD, process, status) \
	SIG(STOP, process, stop) \
	SIG(CONT, process, continue) \
	SIG(TERM, process, terminate) \
	SIG(INT, process, interrupt) \
	SIG(KILL, process, kill) \
	SIG(QUIT, process, quit) \
	\
	SIG(XCPU, limit, cpu) \
	SIG(XFSZ, limit, file) \
	SIG(ALRM, limit, time) \
	SIG(VTALRM, limit, virtual) \
	SIG(PROF, limit, profiling) \
	\
	SIG(HUP, terminal, closed) \
	SIG(TSTP, terminal, stop) \
	SIG(INFO, terminal, query) \
	SIG(WINCH, terminal, delta) \
	SIG(TTIN, terminal, background-read) \
	SIG(TTOU, terminal, background-write) \
	\
	SIG(USR1, event, user-1) \
	SIG(USR2, event, user-2) \
	SIG(URG, event, urgent-condition) \
	SIG(IO, event, io) \
	SIG(TRAP, event, trap) \
	\
	SIG(FPE, exception, floating-point) \
	SIG(PIPE, exception, broken-pipe) \
	\
	SIG(BUS, error, invalid-memory-access) \
	SIG(SEGV, error, restricted-memory-access) \
	SIG(ILL, error, invalid-instruction) \
	SIG(SYS, error, invalid-system-call)
#endif
