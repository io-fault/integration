/**
	// Signal table macro providing categorized signal identifiers
	// and protection against missing signal defines for commonly
	// used signals.
*/
#ifndef _FAULT_POSIX_SIGNAL_H_included_
#define _FAULT_POSIX_SIGNAL_H_included_

/**
	// Macro providing a list of common signals with
	// a categorized descriptive name.
*/
#define PROCESS_SIGNAL_LIST() \
	SIG(INT, process, interrupt) \
	SIG(CHLD, process, status) \
	SIG(STOP, process, stop) \
	SIG(CONT, process, continue) \
	SIG(TERM, process, terminate) \
	SIG(KILL, process, kill) \
	SIG(QUIT, process, quit) \
	\
	SIG(XCPU, limit, cpu) \
	SIG(XFSZ, limit, file) \
	SIG(ALRM, limit, time) \
	SIG(PROF, limit, profiling) \
	SIG(VTALRM, limit, virtual) \
	\
	SIG(HUP, terminal, closed) \
	SIG(TSTP, terminal, stop) \
	SIG(INFO, terminal, query) \
	SIG(TTIN, terminal, background-read) \
	SIG(TTOU, terminal, background-write) \
	SIG(WINCH, terminal, delta) \
	\
	SIG(IO, event, io) \
	SIG(URG, event, urgent-condition) \
	SIG(TRAP, event, trap) \
	SIG(USR1, event, user-1) \
	SIG(USR2, event, user-2) \
	\
	SIG(FPE, exception, floating-point) \
	SIG(PIPE, exception, broken-pipe) \
	\
	SIG(SEGV, error, restricted-memory-access) \
	SIG(BUS, error, invalid-memory-access) \
	SIG(ILL, error, invalid-instruction) \
	SIG(SYS, error, invalid-system-call)
#endif
