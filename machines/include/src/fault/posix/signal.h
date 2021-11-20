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
	SIG(process, status, SIGCHLD) \
	SIG(process, stop, SIGSTOP) \
	SIG(process, continue, SIGCONT) \
	SIG(process, terminate, SIGTERM) \
	SIG(process, interrupt, SIGINT) \
	SIG(process, kill, SIGKILL) \
	SIG(process, quit, SIGQUIT) \
	\
	SIG(limit, cpu, SIGXCPU) \
	SIG(limit, file, SIGXFSZ) \
	SIG(limit, time, SIGALRM) \
	SIG(limit, virtual, SIGVTALRM) \
	SIG(limit, profiling, SIGPROF) \
	\
	SIG(terminal, closed, SIGHUP) \
	SIG(terminal, stop, SIGTSTP) \
	SIG(terminal, query, SIGINFO) \
	SIG(terminal, delta, SIGWINCH) \
	SIG(terminal, background-read, SIGTTIN) \
	SIG(terminal, background-write, SIGTTOU) \
	\
	SIG(event, user-1, SIGUSR1) \
	SIG(event, user-2, SIGUSR2) \
	SIG(event, urgent-condition, SIGURG) \
	SIG(event, io, SIGIO) \
	SIG(event, trap, SIGTRAP) \
	\
	SIG(exception, floating-point, SIGFPE) \
	SIG(exception, broken-pipe, SIGPIPE) \
	\
	SIG(error, invalid-memory-access, SIGBUS) \
	SIG(error, restricted-memory-access, SIGSEGV) \
	SIG(error, invalid-instruction, SIGILL) \
	SIG(error, invalid-system-call, SIGSYS)

/*
	// Check the compilation environment for the identified signals.
	// If a signal is missing, define it with a contrived code and
	// maybe warn about its absence.

	// Defining these makes `#ifdef SIGNAME` checks turn true when
	// they're not expected to. Including this
	// header requires that specific signal checks be rewritten as
	// `#if SIGNAME > 0`.

	// The purpose of these contrived signal codes is to allow
	// the &FAULT_SIGNAL_LIST to be safely expanded as a switch.
*/

#if __ALWAYS__(process)
	#ifndef SIGCHLD
		#warning SIGCHLD not defined.
		#define SIGCHLD (-2)
	#endif

	#ifndef SIGCONT
		#warning SIGCONT not defined.
		#define SIGCONT (-3)
	#endif

	#ifndef SIGSTOP
		#warning SIGSTOP not defined.
		#define SIGSTOP (-4)
	#endif

	#ifndef SIGTERM
		#warning SIGTERM not defined.
		#define SIGTERM (-7)
	#endif

	#ifndef SIGINT
		#warning SIGINT not defined.
		#define SIGINT (-8)
	#endif

	#ifndef SIGKILL
		#warning SIGKILL not defined.
		#define SIGKILL (-9)
	#endif

	#ifndef SIGQUIT
		#warning SIGQUIT not defined.
		#define SIGQUIT (-5)
	#endif

	#ifndef SIGABRT
		#warning SIGABRT not defined.
		#define SIGABRT (-6)
	#endif
#endif

#if __ALWAYS__(terminal)
	#ifndef SIGTSTP
		#warning SIGTSTP not defined.
		#define SIGTSTP (-13)
	#endif

	#ifndef SIGHUP
		#warning SIGHUP not defined.
		#define SIGHUP (-14)
	#endif

	#ifndef SIGINFO
		#define SIGINFO (-15)
	#endif

	#ifndef SIGWINCH
		#define SIGWINCH (-16)
	#endif

	#ifndef SIGTTIN
		#define SIGTTIN (-17)
	#endif

	#ifndef SIGTTOU
		#define SIGTTOU (-18)
	#endif
#endif

#if __ALWAYS__(event)
	#ifndef SIGUSR1
		#warning SIGUSR1 not defined.
		#define SIGUSR1 (-21)
	#endif

	#ifndef SIGUSR2
		#warning SIGUSR2 not defined.
		#define SIGUSR2 (-22)
	#endif

	#ifndef SIGURG
		#define SIGURG (-25)
	#endif

	#ifndef SIGIO
		#define SIGIO (-26)
	#endif

	#ifndef SIGTRAP
		#define SIGTRAP (-29)
	#endif
#endif

#if __ALWAYS__(limits)
	#ifndef SIGALRM
		#define SIGALRM (-31)
	#endif

	#ifndef SIGXCPU
		#define SIGXCPU (-32)
	#endif

	#ifndef SIGXFSZ
		#define SIGXFSZ (-33)
	#endif

	#ifndef SIGVTALRM
		#define SIGVTALRM (-34)
	#endif

	#ifndef SIGPROF
		#define SIGPROF (-35)
	#endif
#endif

#if __ALWAYS__(exception)
	#ifndef SIGFPE
		#warning SIGFPE not defined.
		#define SIGFPE (-41)
	#endif

	#ifndef SIGPIPE
		#warning SIGPIPE not defined.
		#define SIGPIPE (-42)
	#endif
#endif

#if __ALWAYS__(error)
	#ifndef SIGBUS
		#define SIGBUS (-51)
	#endif

	#ifndef SIGSEGV
		#define SIGSEGV (-52)
	#endif

	#ifndef SIGILL
		#define SIGILL (-55)
	#endif

	#ifndef SIGSYS
		#define SIGSYS (-56)
	#endif
#endif
#endif
