/**
	// Definition set compensating for missing signals.

	// On platforms where not all signals are defined, this header can be used
	// to maintain the invariant when building signal switches. Often best used
	// in complete isolation as the definition of absent signals will break
	// the usual `#ifdef` usage.
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
