/**
	// Contend and Conclude Test Protocol implementation for C.

	// [ Usage ]

	// Aside from `equality`, `truth`, and a couple others, the default contentions are
	// named after their corresponding libc function and maintain their interface.

	// #!syntax/c
		//// By default, everything needed to compile an executable is included and defined.
		#include <fault/test.h>

		//// Define a new test; the macro argument is appended to `test_` to
		//// form the function's name. All symbols starting with `test_` should
		//// be test functions. (`test_feature` function is being defined here.)
		Test(feature)
		{
			if (feature_available == false)
				test->skip("feature not available");

			test(function() == 100); // test->truth() shorthand.
			test->equality(10, 10); // test(10 == 10), but with operand strings in errors.

			// Inversion. Operands must not be equal.
			test(!)->equality(10, 15);

			// Returns what strcmp() returns when valid.
			test->strcmp("IdNameString", lookup_name(id));
			// Returns what strstr() returns when needle is found.
			test->strstr("haystack of needles", "needle");

			if (thats_not_right)
				test->fail("formatted message");
		}

	// If multiple sources are being compiled into the same target, the
	// `TEST_SUITE_EXTENSION` define should be set in all but one source
	// file that includes `test.h`:

	// #!syntax/c
		//// Stop some globals from being defined here as it's being
		//// joined with the source object that defines them.
		#define TEST_SUITE_EXTENSION
		#include <fault/test.h>

		Test(feature)
		{
			test->fail(...)
		}

	// [ Test Control Methods ]

	// Most of the methods are named directly after their corresponding libc function
	// and intend to provide an identical interface. Consistent return values
	// are provided in cases where absurdities did not cause the test to conclude.

	// /`test->truth(int)`/
		// Fail when zero. Method form of `test(expr)`.

	// /`test->equality(intmax_t, intmax_t)`/
		// Fail when integers are not equal.

	// /`test->strcmpf(const char *solution, const char *format, ...)`/
		// Fail when the formatted string is not equal to the solution.

	// /`test->strcmp(const char *, const char *)`/
		// Fail when the strings are not equal.

	// /`test->strcasecmp(const char *, const char *)`/
		// Fail when, case insensitive, strings are not equal.

	// /`test->strstr(const char *haystack, const char *needle)`/
		// Fail when the needle string is not found in haystack.

	// /`test->strcasestr(const char *haystack, const char *needle)`/
		// Fail when the, case insensitive, needle is not found in haystack.

	// /`test->wcscmp(const wchar_t *, const wchar_t *)`/
		// Fail when strings are not equal.

	// /`test->wcscasecmp(const wchar_t *, const wchar_t *)`/
		// Fail when, case insensitive, strings are not equal.

	// /`test->wcsstr(const wchar_t *haystack, const wchar_t *needle)`/
		// Fail when the, wide character, needle is not found in haystack.

	// /`test->memcmp(void *, void *, size_t)`/
		// Fail when the bytes of memory references are not equal.

	// /`test->memchr(void *memory, int byte, size_t memory_size)`/
		// Fail when the byte could not be found in memory.

	// /`test->memrchr(void *memory, int byte, size_t memory_size)`/
		// Fail when the byte could not be found in memory with the
		// search starting at the end.

	// [ Inverse Contentions ]

	// Inversion of a contention can be performed with the not (!) test modifier:
	// `test(!)`. When the &test macro is called this way, the test context is
	// configured to invert the effect of the next contention.

	// #!syntax/c
		Test(feature)
		{
			test(!)->equality(10, 15); // 10 != 15
			test(!)->strcmp("a", "b"); // "a" != "b"

			//// The inversion may occur independently of the contention as well:
			test(!);
			test->memchr("sixty", 'z', 5); // 'z' not in "sixty"
		}

	// [ Tracing Contentions ]

	// Tracing of contentions can be performed with the tilde (~) test modifier:
	// `test(~)`. When the &test macro is called this way, the test context is
	// configured to emit a trace message of the next contention displaying
	// information similar to what would be found in a failure message.
	// Trace messages are only emitted when called for and the test is not
	// being concluded.

	// #!syntax/c
		Test(feature)
		{
			test(~)->strcmpf("expected 100", "expected %s", subject(...));
		}

	// Tracing may be combined with inversion by appending the tilde:

	// #!syntax/c
		Test(feature)
		{
			//// `!~` only. `~!` is not recognized.
			test(!~)->equality(10, 20);
		}

	// [ Forcing and Ignoring Absurdities ]

	// The negative (-) and positive (+) modifiers force and disable failure conclusions.
	// With negative forcing failure and positive forcing success. Their utility is
	// a minor niche that would usually be filled with merely commenting out the
	// contentions or inserting explicit failure. However, they offer some convenience by
	// performing those tasks without any restructuring.

	// #!syntax/c
		Test(feature)
		{
			//// Fails, but the following contention
			//// is of interest, so disable the conclusion.
			test(+)->strcmp("expectation", missed());

			//// Force failure here to inspect its arguments and
			//// to avoid running anything afterwards.
			test(-)->equality(0, innerfunction());

			//// ...
		}

	// Like inversion, tracing may be combined with forced success by appending the
	// tilde: `test(+~)`. No modifier combination is provided for forced failure as
	// the message is already being printed.

	// [ Integration Control Defines ]

	// /`TEST_SUITE_IDENTITY`/
		// String identifying the set of tests.
	// /`TEST_SUITE_EXTENSION`/
		// Definition used to signal the (test.h) header that the source should not
		// define global storage variables or the main function.

		// When compiling multiple sources, all but one source file should define this
		// before including `test.h`. The default presumption of the primary is to allow
		// for minimum information usage of the test framework.

		// Given heavy usage of multiples sources, conditionally defaulting the definition of
		// `TEST_SUITE_EXTENSION` in a header that then includes `test.h` or
		// including the extensions directly in the primary source file can eliminate
		// the redundancy.

		// Implies `TEST_DISABLE_MAIN`.
	// /`TEST_DISABLE_MAIN`/
		// Don't define the default main function for executing tests.

		// Only used, directly, in cases where execution is being handled by
		// another library or source file that is independent of the tests being
		// compiled.
	// /`TEST_DISABLE_INVASIVE_CONTROLS`/
		// Disable many control macros providing test control context information
		// in cases of contended absurdities(C Preprocessor provided location information).
		// While `strcmp`, `strcasecmp`, and `memcmp` have resolution proxies so that they
		// may be used directly, methods like `pass`, `fail`, and `skip` could easily cause
		// conflicts without tangible resolutions as there are no standard forms to adapt to.
	// /`TEST_DISABLE_DEFAULT_INCLUDES`/
		// Presume availability of the necessary C environment.
	// /`TEST_STATUS_FRAME_RECEIVER`/
		// The file descriptor to write status frames to. Defaults to `STDOUT_FILENO`.
	// /`TEST_FS_TMPDIR_ROOT`/
		// Default root directory for temporary file storage. `/tmp/` by default, and
		// only used when (system/environ)`TMPDIR` is unset.
	// /`TEST_FS_RM_PATH`/
		// Path to `rm` binary for temporary directory cleanup.
*/
#ifndef _FAULT_TEST_H_
#define _FAULT_TEST_H_

#if !defined(TEST_STATUS_FRAME_RECEIVER)
	#define TEST_STATUS_FRAME_RECEIVER STDOUT_FILENO
#endif

#if !defined(TEST_DISABLE_DEFAULT_INCLUDES)
	#include <assert.h>
	#include <stdio.h>
	#include <stdarg.h>
	#include <string.h>
	#include <setjmp.h>
	#include <stdlib.h>
	#include <stdbool.h>
	#include <unistd.h>
	#include <inttypes.h>
	#include <wchar.h>
	#include <fcntl.h>
	#include <errno.h>
	#include <sys/stat.h>
	#include <sys/wait.h>
	#include <sys/uio.h>
	#include <sys/types.h>
	#include <sys/time.h>
	#include <sys/resource.h>

	#include "utf-8.h"
	#include "clock.h"
	#include "base-64.h"
	#include "status.h"
#endif

/**
	// C++ compatibility.
*/
#ifdef __cplusplus
	#ifndef _TEST_SYMBOL_QUALIFIER
		// Avoid any name mangling of test functions to guarantee "test_*" symbols.
		#define _TEST_SYMBOL_QUALIFIER extern "C"
	#endif
#endif

#ifndef _TEST_SYMBOL_QUALIFIER
	// No qualification needed for C.
	#define _TEST_SYMBOL_QUALIFIER
#endif

#ifndef TEST_FS_TMPDIR_ROOT
	#define TEST_FS_TMPDIR_ROOT "/tmp/"
#endif

#ifndef TEST_FS_RM_PATH
	#define TEST_FS_RM_PATH "/bin/rm"
#endif

#if defined(__APPLE__) && !defined(TEST_DISABLE_LOCAL_MEMRCHR)
	// Not found in recent (2025) macOS versions.
	static inline void *
	memrchr(void *memory, int c, size_t s)
	{
		const char *bytes = (const char *) memory;
		const char b = c;
		bytes += s;

		while (bytes != memory)
		{
			bytes -= 1;

			if (*bytes == b)
				return((void *) bytes);
		}

		return(NULL);
	}
#endif

/**
	// The methods used to run test functions.

	// /td_sequential/
		// One test at a time in a single process.
		// &siglongjmp is used to exit concluded tests.
	// /td_thread/
		// Dispatch the test in a thread.
		// &pthread_exit is used to exit tests.
	// /td_process/
		// Dispatch the test in a forked process.
		// &exit is used to exit tests.
*/
enum TestDispatchStrategy {
	td_sequential,
	td_thread,
	td_process
};

/**
	// Identifying information about the test.

	// [ Elements ]
	// /ti_name/
		// The base name of the test.
	// /ti_symbol/
		// The name of the test function's symbol; &ti_name with `test_` prefix.
	// /ti_source/
		// The file that the test was defined in.
	// /ti_line_string/
		// The line number of the test's declaration as a string.
	// /ti_line/
		// The line number of the test's declaration.
	// /ti_index/
		// The __COUNTER__ value when the test was declared.
*/
struct TestIdentity {
	const char *ti_name;
	const char *ti_symbol;
	const char *ti_source;
	const char *ti_line_string;
	int ti_line;
	int ti_index;
};

/**
	// Test conclusions. Isolated from failure types to simplify counts.

	// [ Elements ]
	// /tc_failed/
		// The test did not pass.
	// /tc_skipped/
		// The test was not ran at all. Normally, due to relevance such as
		// a platform specific test or a missing feature.
	// /tc_passed/
		// The test passed.
*/
enum TestConclusion {
	tc_failed  = -1,
	tc_skipped =  0,
	tc_passed  = +1,
};

/**
	// Failure classification; none when tc_skipped or tc_passed.

	// [ Elements ]
	// /tf_none/
		// Failure was not concluded.
	// /tf_absurdity/
		// Failure was concluded by a contended absurdity.
	// /tf_limit/
		// Harness enforced resource limitation.
	// /tf_interrupt/
		// Test process received a signal requesting termination.
		// Normally, this will be POSIX signals, but the harness may support
		// other sources.
	// /tf_explicit/
		// Failure was directly concluded, `test->fail(msg)`.
	// /tf_fault/
		// Fault detected or trapped during testing.
		// Critical process signal(SIGSEGV), language exception,
		// or a promoted application error.
*/
enum FailureType {
	tf_limit     = -3,
	tf_interrupt = -2,
	tf_explicit  = -1,
	tf_none      =  0,
	tf_absurdity = +1,
	tf_fault     = +2,
};

/**
	// Overrides for the effect of the contention.

	// [ Elements ]
	// /ac_reflect/
		// No change. Contending absurdity will conclude failure.
	// /ac_never/
		// Never fail the test under this contention.
	// /ac_invert/
		// Absurdity inversion. Absurdities are truth and truths are
		// considered absurd.
	// /ac_always/
		// Always fail the test under this contention.
*/
enum AbsurdityControl {
	ac_never = -2,
	ac_always = -1,
	ac_reflect = 0,
	ac_invert
};

static inline bool
_test_absurdity_control(enum AbsurdityControl delta, bool absurdity)
{
	switch (delta)
	{
		case ac_reflect:
			return(absurdity);
		case ac_never:
			return(false);
		case ac_always:
			return(true);
		case ac_invert:
			return(!absurdity);
	}
}

static inline const char *
_test_representation(enum AbsurdityControl delta)
{
	switch (delta)
	{
		case ac_reflect:
			return("test");
		case ac_never:
			return("test(+)");
		case ac_always:
			return("test(-)");
		case ac_invert:
			return("test(!)");
	}
}

/**
	// Argument lists providing access to parameter names.
*/
#define _FTA_UNARY_PATH(ARGS) ARGS(path)
#define _FTA_BINARY(ARGS) ARGS(solution, candidate)
#define _FTA_BINARY_1L(ARGS) ARGS(solution, candidate, length)
#define _FTA_BINARY_FMT(ARGS) ARGS(_test_format_arguments, solution, candidate)
#define _FTA_FORMAT(ARGS) ARGS(format)

#define _FT_VA_DOTS ...
#define _FT_ARGUMENTS(ARGLIST, ...) ARGLIST (_ECHO)
#define _FT_RETURN(AL, RTYPE, ...) RTYPE
#define _FT_PARAMETERS(AL, RTYPE, ...) __VA_ARGS__

#define _LOG_T(FT) FT(_FTA_FORMAT, int, const char *format, _FT_VA_DOTS)
#define _INTCMP_T(FT) FT(_FTA_BINARY, int, intmax_t solution, intmax_t candidate)
#define _INTCMPF_T(FT) FT(_FTA_BINARY_FMT, int, _test_format_parameters, intmax_t solution, intmax_t candidate)
#define _STRCMP_T(FT) FT(_FTA_BINARY, int, const char *solution, const char *candidate)
#define _STRCMPF_T(FT) FT(_FTA_BINARY, int, const char *solution, const char *candidate, _FT_VA_DOTS)
#define _STRSTR_T(FT) FT(_FTA_BINARY, char *, const char *solution, const char *candidate)
#define _MEMCMP_T(FT) FT(_FTA_BINARY_1L, int, void *solution, void *candidate, size_t length)
#define _MEMCHR_T(FT) FT(_FTA_BINARY_1L, void *, void *solution, int candidate, size_t length)
#define _LSTRSTR_T(FT) FT(_FTA_BINARY, wchar_t *, const wchar_t *solution, const wchar_t *candidate)
#define _LSTRCMP_T(FT) FT(_FTA_BINARY, int, const wchar_t *solution, const wchar_t *candidate)

#define _LOG_SF(SYMBOL) _tci_##SYMBOL##_test
#define _CONTEND_SF(SYMBOL) _tci_contend_##SYMBOL

#define _ECHO(...) __VA_ARGS__
#define _WRAP(...) (__VA_ARGS__)
#define _FIRST(N, ...) N

#define TEST_CONTROL_METHODS(CONTEXT, TM) \
	TM(CONTEXT, fail, _LOG_SF, _LOG_T) \
	TM(CONTEXT, skip, _LOG_SF, _LOG_T) \
	TM(CONTEXT, pass, _LOG_SF, _LOG_T) \
	TM(CONTEXT, truth, _CONTEND_SF, _INTCMP_T) \
	TM(CONTEXT, equality, _CONTEND_SF, _INTCMPF_T) \
	TM(CONTEXT, strstr, _CONTEND_SF, _STRSTR_T) \
	TM(CONTEXT, strcasestr, _CONTEND_SF, _STRSTR_T) \
	TM(CONTEXT, strcmp, _CONTEND_SF, _STRCMP_T) \
	TM(CONTEXT, strcasecmp, _CONTEND_SF, _STRCMP_T) \
	TM(CONTEXT, wcsstr, _CONTEND_SF, _LSTRSTR_T) \
	TM(CONTEXT, wcscmp, _CONTEND_SF, _LSTRCMP_T) \
	TM(CONTEXT, wcscasecmp, _CONTEND_SF, _LSTRCMP_T) \
	TM(CONTEXT, memchr, _CONTEND_SF, _MEMCHR_T) \
	TM(CONTEXT, memrchr, _CONTEND_SF, _MEMCHR_T) \
	TM(CONTEXT, memcmp, _CONTEND_SF, _MEMCMP_T) \
	TM(CONTEXT, strcmpf, _CONTEND_SF, _STRCMPF_T)

#define _location_arguments path, ln, fn
#define _location_parameters const char *path, int ln, const char *fn
#define _test_control_operand_parameters const char *former, const char *latter

#define _test_control_location __FILE__, __LINE__, __func__
#define _test_control_operands former, latter

#define _test_control_macro_arguments test, _test_control_location
#define _test_control_arguments test, path, ln, fn, _test_control_operands
#define _test_context_parameters \
	struct Test * __attribute__((nonnull)) test, _location_parameters
#define _test_control_parameters \
	_test_context_parameters, _test_control_operand_parameters
#define _test_format_arguments opstr, fofmt, lofmt
#define _test_format_parameters const char *opstr, const char *fofmt, const char *lofmt

struct Test;
struct TestControls {
	#define TEST_METHOD_DECLARATIONS(CTX, METHOD, STYPE, FTYPE) \
		FTYPE(_FT_RETURN) (* METHOD)(_test_control_parameters, FTYPE(_FT_PARAMETERS));

		TEST_CONTROL_METHODS(void, TEST_METHOD_DECLARATIONS)
	#undef TEST_METHOD_DECLARATIONS

	const char * (*fs_tmp)(_test_context_parameters, const char *);
	int (*exit)(struct Test *);
};

struct Test {
	// Keeping the test controls allocation with the start of Test to
	// minimize the difficulty of aligning compatible methods.
	struct TestControls _controls;
	struct TestControls *controls;

	// Provided by the HarnessTestRecord
	struct TestIdentity *identity;

	uint64_t tmpdir_path_hash;
	char *tmpdir_path;

	// Exposed, but only used by control methods.
	uint64_t contentions;
	bool contention_trace;
	enum AbsurdityControl contention_delta:4;
	enum TestConclusion conclusion:4;
	enum FailureType failure:4;

	// As recognized by the control macros.
	// Filled when a test is concluded.
	int stf_receiver;
	const char *source_path;
	uint32_t source_line_number;
	const char *function_name;
	const char *operands[2];

	const char *cause;
	const char *report;
};

/**
	// Trace contention.
*/
static inline struct Test *
_test_trace_contention(struct Test *t)
{
	t->contention_trace = true;
	return(t);
}

/**
	// Reconfigure the &Test.contention_delta.
	// Failure is success. Success is failure.
*/
static inline struct Test *
_test_invert_delta(struct Test *t)
{
	switch (t->contention_delta)
	{
		case ac_reflect:
			t->contention_delta = ac_invert;
		break;
		case ac_invert:
			t->contention_delta = ac_reflect;
		break;
		case ac_always:
			t->contention_delta = ac_never;
		break;
		case ac_never:
			t->contention_delta = ac_always;
		break;
	}
	return(t);
}

/**
	// Force absurdity.
*/
static inline struct Test *
_test_always_fail(struct Test *t)
{
	t->contention_delta = ac_always;
	return(t);
}

/**
	// Force true contention.
*/
static inline struct Test *
_test_never_fail(struct Test *t)
{
	t->contention_delta = ac_never;
	return(t);
}

/**
	// The proxies exist as (name) conflicting macros are used to get
	// C preprocessor based location data and argument strings when
	// contentions are performed. In order for `test->memcmp(...)` to
	// get location context, `memcmp()` must be defined.

	// When the conflicting macro is invoked out of `test->` context, the
	// proxies are selected via the global, `controls` and the intended
	// functionality should be performed.
*/
#define TEST_CONTROL_PROXIES(TCP) \
	TCP(memcmp, _MEMCMP_T) \
	TCP(memchr, _MEMCHR_T) \
	TCP(memrchr, _MEMCHR_T) \
	TCP(strcmp, _STRCMP_T) \
	TCP(strcasecmp, _STRCMP_T) \
	TCP(strstr, _STRSTR_T) \
	TCP(strcasestr, _STRSTR_T) \
	TCP(wcscmp, _LSTRCMP_T) \
	TCP(wcscasecmp, _LSTRCMP_T) \
	TCP(wcsstr, _LSTRSTR_T)

/**
	// Define the static inline proxies for invasive macro compensation.
*/
#define DEFINE_PROXY(FNAME, FTYPE) \
	static inline FTYPE(_FT_RETURN) \
	_##FNAME##_proxy(_test_control_parameters, FTYPE(_FT_PARAMETERS)) \
	{ return((FTYPE(_FT_RETURN)) (FNAME)(FTYPE(_FT_ARGUMENTS))); }

TEST_CONTROL_PROXIES(DEFINE_PROXY)
#undef DEFINE_PROXY

const static struct TestControls _tif_ctlgad = {
	#define PINIT(NAME, TYPE) .NAME = _##NAME##_proxy,
		TEST_CONTROL_PROXIES(PINIT)
	#undef PINIT
};
const static struct Test _tif_tgad = {.controls = (struct TestControls *) &_tif_ctlgad, 0,};

// The globals that catch the invasive macros and route them through the proxies.
const static struct TestControls * const controls = &_tif_ctlgad;
const static struct Test * const test = &_tif_tgad;

typedef void (*TestFunction)(struct Test *);

struct HarnessTestRecord;
struct HarnessTestRecord {
	struct TestIdentity *htr_identity;
	TestFunction htr_pointer;

	struct HarnessTestRecord *previous;
	struct HarnessTestRecord *next;
};

typedef enum TestConclusion (*TestDispatch)
	(int, const char *, int *, struct TestControls *, struct HarnessTestRecord *);
typedef int (*TestExit)(struct Test *);

// Sequential single process dispatch uses this to exit tests upon concluding.
extern sigjmp_buf _h_exit_root;
extern struct HarnessTestRecord _h_function_zero;
extern struct HarnessTestRecord *_h_function_index;

extern const char *_h_tmpdir_restriction;
extern const char *_h_tmpdir_root;

#define _TEST_RECORD_CONSTRUCTOR(NAME, FILE, LINE, INDEX) \
	static void __attribute__((constructor)) \
	_h_##NAME##_add(void) { \
		struct HarnessTestRecord *tfr; \
		struct TestIdentity *ti; \
		\
		tfr = (struct HarnessTestRecord *) malloc(sizeof(struct HarnessTestRecord)); \
		if (tfr == NULL) abort(); \
		ti = (struct TestIdentity *) malloc(sizeof(struct TestIdentity)); \
		if (ti == NULL) abort(); \
		\
		ti->ti_name = #NAME; \
		ti->ti_symbol = "test_" #NAME; \
		ti->ti_source = FILE; \
		ti->ti_line = LINE; \
		ti->ti_line_string = #LINE; \
		ti->ti_index = INDEX; \
		tfr->htr_identity = ti; \
		tfr->htr_pointer = (TestFunction) test_##NAME; \
		tfr->previous = _h_function_index; \
		tfr->next = 0; \
		if (_h_function_index != 0) \
			_h_function_index->next = tfr; \
		_h_function_index = tfr; \
	}

#define _TEST_FUNCTION_DECLARATION(NAME) \
	_TEST_SYMBOL_QUALIFIER void NAME (struct Test *test)

#ifndef __COUNTER__
	#define __COUNTER__ -1
#endif

#define _Test(NAME, INDEX, ...) \
	_TEST_FUNCTION_DECLARATION(test_##NAME); \
	_TEST_RECORD_CONSTRUCTOR(NAME, __FILE__, __LINE__, INDEX) \
	_TEST_FUNCTION_DECLARATION(test_##NAME)
#define Test(NAME, ...) _Test(NAME, __COUNTER__, __VA_ARGS__)

#define _xtfmt(X) _Generic((X), \
	uint64_t: PRIX64, \
	uint32_t: PRIX32, \
	uint16_t: PRIX16, \
	uint8_t: PRIX8 \
	default: "X" \
)

#define _dtfmt(X) _Generic((X), \
	int64_t: PRId64, \
	int32_t: PRId32, \
	int16_t: PRId16, \
	int8_t: PRId8, \
	uint64_t: PRIu64, \
	uint32_t: PRIu32, \
	uint16_t: PRIu16, \
	uint8_t: PRIu8, \
	default: "d" \
)

#define _TEST_FORMATTING(OP, F, L) OP, _dtfmt(F), _dtfmt(L)

/**
	// Supports two forms: `test->MACRO()` and `MACRO()`.
	// Each form needs different isolation as `test->MACRO()` has conflicts (memcmp and others).
*/
#define _TEST_MACRO_DIRECTION(ISOLATION, TEST_CONTROLS, METHOD, ...) \
	ISOLATION(TEST_CONTROLS->METHOD)(_test_control_macro_arguments __VA_OPT__(,) __VA_ARGS__)

#define _TEST_METHOD_FORMAT(S, CTL, METHOD, ...) _TEST_MACRO_DIRECTION(S, CTL, METHOD, "void", "void", __VA_ARGS__)
#define _TEST_METHOD_NONE(S, CTL, METHOD) _TEST_MACRO_DIRECTION(S, CTL, METHOD)
#define _TEST_METHOD_OPTION(S, CTL, METHOD, ...) _TEST_MACRO_DIRECTION(S, CTL, METHOD, _FIRST(__VA_ARGS__ __VA_OPT__(,) NULL))
#define _TEST_METHOD_UNARY(S, CTL, METHOD, A) _TEST_MACRO_DIRECTION(S, CTL, METHOD, #A, "void", A, 0)
#define _TEST_METHOD_BINARY(S, CTL, METHOD, A, B, ...) _TEST_MACRO_DIRECTION(S, CTL, METHOD, #A, #B, A, B __VA_OPT__(,) __VA_ARGS__)
#define _TEST_METHOD_BINARY_F(S, CTL, METHOD, OP, A, B, ...) \
	_TEST_MACRO_DIRECTION(S, CTL, METHOD, #A, #B, _TEST_FORMATTING(OP, A, B), (intmax_t)A, (intmax_t)B)

#define _TEST_EXCLAMATION(Y) ((Y)[0] == '!' && (Y)[1] == 0)
#define _TEST_NEGATIVE(Y) ((Y)[0] == '-' && (Y)[1] == 0)
#define _TEST_POSITIVE(Y) ((Y)[0] == '+' && (Y)[1] == 0)
#define _TEST_TILDE(Y) ((Y)[0] == '~' && (Y)[1] == 0)
#define _TEST_XTILDE(Y) ((Y)[0] == '!' && (Y)[1] == '~' && (Y)[2] == 0)
#define _TEST_PTILDE(Y) ((Y)[0] == '+' && (Y)[1] == '~' && (Y)[2] == 0)
#define _TEST_COALESCE(...) __VA_ARGS__ + 0
#define _TEST_TRUTH(...) \
	(test->controls->truth)(_test_control_macro_arguments, #__VA_ARGS__, "void", _TEST_COALESCE(__VA_ARGS__), 0)
#define test(...) ( \
	_TEST_EXCLAMATION(#__VA_ARGS__) ? _test_invert_delta(test) : \
	_TEST_TILDE(#__VA_ARGS__) ? _test_trace_contention(test) : \
	_TEST_XTILDE(#__VA_ARGS__) ? _test_invert_delta(_test_trace_contention(test)) : \
	_TEST_PTILDE(#__VA_ARGS__) ? _test_never_fail(_test_trace_contention(test)) : \
	_TEST_NEGATIVE(#__VA_ARGS__) ? _test_always_fail(test) : \
	_TEST_POSITIVE(#__VA_ARGS__) ? _test_never_fail(test) : \
	(_TEST_TRUTH(__VA_ARGS__) ? (test) : (test)) \
)

/**
	// Namespace friendly test controls.
*/
#define allocate_fs_tmp(...) _TEST_METHOD_OPTION(_WRAP, test->controls, fs_tmp, __VA_ARGS__)

#define fail_test(...) _TEST_METHOD_FAIL(_WRAP, test->controls, fail, __VA_ARGS__)
#define skip_test(...) _TEST_METHOD_SKIP(_WRAP, test->controls, skip, __VA_ARGS__)
#define pass_test(...) _TEST_METHOD_PASS(_WRAP, test->controls, pass, __VA_ARGS__)

#define contend_truth(...) _TEST_METHOD_UNARY(_WRAP, test->controls, truth, __VA_ARGS__)
#define contend_equality(...) _TEST_METHOD_BINARY_F(_WRAP, test->controls, equality, "!=", __VA_ARGS__)

#define contend_memcmp(...) _TEST_METHOD_BINARY(_WRAP, test->controls, memcmp, __VA_ARGS__)
#define contend_memchr(...) _TEST_METHOD_BINARY(_WRAP, test->controls, memchr, __VA_ARGS__)
#define contend_memrchr(...) _TEST_METHOD_BINARY(_WRAP, test->controls, memrchr, __VA_ARGS__)

#define contend_strstr(...) _TEST_METHOD_BINARY(_WRAP, test->controls, strstr, __VA_ARGS__)
#define contend_strcasestr(...) _TEST_METHOD_BINARY(_WRAP, test->controls, strcasestr, __VA_ARGS__)
#define contend_strcmp(...) _TEST_METHOD_BINARY(_WRAP, test->controls, strcmp, __VA_ARGS__)
#define contend_strcasecmp(...) _TEST_METHOD_BINARY(_WRAP, test->controls, strcasecmp, __VA_ARGS__)
#define contend_strcmpf(...) _TEST_METHOD_BINARY(_WRAP, test->controls, strcmpf, __VA_ARGS__)

#define contend_wcscmp(...) _TEST_METHOD_BINARY(_WRAP, test->controls, wcscmp, __VA_ARGS__)
#define contend_wcscasecmp(...) _TEST_METHOD_BINARY(_WRAP, test->controls, wcscasecmp, __VA_ARGS__)
#define contend_wcsstr(...) _TEST_METHOD_BINARY(_WRAP, test->controls, wcsstr, __VA_ARGS__)

/**
	// Invasive test controls that allow for a syntax that is compatible
	// with simple structure abstractions.
*/
#if !defined(TEST_DISABLE_INVASIVE_CONTROLS)
	#define fs_tmp(...) _TEST_METHOD_OPTION(_ECHO, controls, fs_tmp, __VA_ARGS__)
	#define fail(...) _TEST_METHOD_FORMAT(_ECHO, controls, fail, __VA_ARGS__)
	#define skip(...) _TEST_METHOD_FORMAT(_ECHO, controls, skip, __VA_ARGS__)
	#define pass(...) _TEST_METHOD_FORMAT(_ECHO, controls, pass, __VA_ARGS__)

	#define truth(...) _TEST_METHOD_UNARY(_ECHO, controls, truth, __VA_ARGS__)
	#define equality(...) _TEST_METHOD_BINARY_F(_ECHO, controls, equality, "!=", __VA_ARGS__)

	#define memcmp(...) _TEST_METHOD_BINARY(_ECHO, controls, memcmp, __VA_ARGS__)
	#define memchr(...) _TEST_METHOD_BINARY(_ECHO, controls, memchr, __VA_ARGS__)
	#define memrchr(...) _TEST_METHOD_BINARY(_ECHO, controls, memrchr, __VA_ARGS__)

	#define strstr(...) _TEST_METHOD_BINARY(_ECHO, controls, strstr, __VA_ARGS__)
	#define strcasestr(...) _TEST_METHOD_BINARY(_ECHO, controls, strcasestr, __VA_ARGS__)
	#define strcmp(...) _TEST_METHOD_BINARY(_ECHO, controls, strcmp, __VA_ARGS__)
	#define strcasecmp(...) _TEST_METHOD_BINARY(_ECHO, controls, strcasecmp, __VA_ARGS__)
	#define strcmpf(...) _TEST_METHOD_BINARY(_ECHO, controls, strcmpf, __VA_ARGS__)

	#define wcscmp(...) _TEST_METHOD_BINARY(_ECHO, controls, wcscmp, __VA_ARGS__)
	#define wcscasecmp(...) _TEST_METHOD_BINARY(_ECHO, controls, wcscasecmp, __VA_ARGS__)
	#define wcsstr(...) _TEST_METHOD_BINARY(_ECHO, controls, wcsstr, __VA_ARGS__)
#endif

static inline uint64_t
_h_hash_string(const char *string)
{
	static const uint64_t init = 0xf1fade1f << 32 | 0xf1fade1f;
	size_t length = strlen(string);
	uint8_t r = length % sizeof(uint64_t);
	uint64_t h = init;
	uint64_t final = 0;
	uint64_t *uv = (uint64_t *) string;
	uint64_t s = 0;

	for (int i = 0; i < length / sizeof(uint64_t); ++i)
	{
		if (uv[i] == 0)
		{
			++s;
			h ^= (s * 0x0102030405060708);
		}
		else
			h ^= (uv[i] * 0x0102030405060708);
	}

	string += length - r;
	while (*string)
	{
		final |= (uint8_t) *string;
		final <<= 8;
		++string;
	}

	if (final == 0)
	{
		++s;
		h ^= (s * 0x0102030405060708);
	}
	else
		h ^= (final * 0x0102030405060708);

	return(h);
};

static inline void
h_conclude_test(enum TestConclusion tc, enum FailureType ft, _test_control_parameters)
{
	test->conclusion = tc;
	test->failure = ft;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = former;
	test->operands[1] = latter;
}


static inline const char *
_h_allocatef(const char *fmt, ...)
{
	char *s = NULL;
	int r;
	va_list vl;

	va_start(vl, fmt);
	r = vasprintf(&s, fmt, vl);
	va_end(vl);

	return(s);
}

#define _h_cause(fmt, ...) (fmt, __VA_ARGS__)
#define _h_report(fmt, ...) (fmt, __VA_ARGS__)
#define _h_insert_location(srcpath, srcln) \
	TTYN_INSERT_CONSTANT("\tLOCATION: line "), \
	TTYN_INSERT_DECIMAL(srcln), \
	TTYN_INSERT_CONSTANT(" in \""), \
	TTYN_INSERT_STRING(srcpath), \
	TTYN_INSERT_CONSTANT("\"")

#define _h_print_note(T, A, R) do { \
	if (T->failure) \
	{ \
		T->cause = _h_allocatef A; \
		T->report = _h_allocatef R; \
	} \
	else \
	{ \
		char *icause = NULL, *ireport = NULL; \
		size_t cause_len, report_len; \
		const char *cause = _h_allocatef A; \
		const char *report = _h_allocatef R; \
		\
		cause_len = stf_indent_text((uint8_t **) &icause, (stf_string_t) cause, strlen(cause) + 1, 8, 1); \
		report_len = stf_indent_text((uint8_t **) &ireport, (stf_string_t) report, strlen(report) + 1, 8, 1); \
		free((void *) cause); \
		free((void *) report); \
		\
		ttyn1_log_trace( \
			T->stf_receiver, NULL, \
			T->identity->ti_symbol, T->identity->ti_symbol, \
			TTYN_SYNOPSIS A, TTYN_EXTENSION( \
				TTYN_INSERT_SECTION("@operation", "test-contention"), \
				TTYN_INSERT(cause_len-1, icause), \
				TTYN_INSERT_NEWLINE, \
				_h_insert_location(T->source_path, T->source_line_number), \
				TTYN_INSERT_NEWLINE, \
				TTYN_INSERT_SECTION("@report", "test-trace"), \
				TTYN_INSERT(report_len-1, ireport), \
				TTYN_INSERT_NEWLINE \
			) \
		); \
		\
		free(icause); \
		free(ireport); \
	} \
} while(0)

static inline const char *
_tci_fs_tmp(_test_context_parameters, const char *tmpdir_root)
{
	const char *former = tmpdir_root;
	const char *latter = "";
	const char *slash = "";
	int length;

	// Already initialized.
	// Don't bother re-creating if the test chose to delete it.
	if (test->tmpdir_path != NULL)
		return(test->tmpdir_path);

	// TMPDIR configuration issue.
	if (tmpdir_root == NULL)
	{
		if (_h_tmpdir_restriction != NULL)
		{
			h_conclude_test(tc_failed, tf_limit, _test_control_arguments);
			if (tmpdir_root != NULL)
				test->cause = _h_allocatef("%s: test->fs_tmp(\"%s\")", tmpdir_root);
			else
				test->cause = _h_allocatef("%s: test->fs_tmp()", _h_tmpdir_restriction);
			test->report = _h_allocatef("TMPDIR: %s", _h_tmpdir_root);

			errno = 0;
			test->controls->exit(test);
			return(NULL);
		}

		tmpdir_root = _h_tmpdir_root;
	}

	// Insert slash if missing.
	if (tmpdir_root[0] != 0 && tmpdir_root[strlen(tmpdir_root)-1] != '/')
		slash = "/";

	length = asprintf(&test->tmpdir_path, "%s%s%s.XXXXXXXX",
		tmpdir_root, slash, test->identity->ti_symbol);
	if (length >= 0)
	{
		if (mkdtemp(test->tmpdir_path) == NULL)
		{
			free((void *) test->tmpdir_path);
			test->tmpdir_path = NULL;
		}
		else
		{
			// Some protection against memory corruption scribbling on the tmpdir_path.
			test->tmpdir_path_hash = _h_hash_string(test->tmpdir_path);
		}
	}
	else if (errno == 0)
		errno = ENOMEM;

	if (test->tmpdir_path == NULL)
	{
		h_conclude_test(tc_failed, tf_fault, _test_control_arguments);
		test->cause = _h_allocatef("could not create temporary directory for test.");
		test->report = _h_allocatef("SYSTEM: %s", strerror(errno));

		errno = 0;
		test->controls->exit(test);
	}

	return(test->tmpdir_path);
}

static inline int
_tci_fail_test(_test_control_parameters, const char *format, ...)
{
	va_list vl;

	test->conclusion = tc_failed;
	test->failure = tf_explicit;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = 0;
	test->operands[1] = 0;

	va_start(vl, format);
	vasprintf((char **) &test->report, format, vl);
	va_end(vl);
	asprintf((char **) &test->cause, "test->fail()");

	test->controls->exit(test);
	return(0);
}

static inline int
_tci_skip_test(_test_control_parameters, const char *format, ...)
{
	va_list vl;

	test->conclusion = tc_skipped;
	test->failure = tf_none;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = 0;
	test->operands[1] = 0;

	va_start(vl, format);
	vasprintf((char **) &test->report, format, vl);
	va_end(vl);
	asprintf((char **) &test->cause, "test->skip()");

	test->controls->exit(test);
	return(0);
}

static inline int
_tci_pass_test(_test_control_parameters, const char *format, ...)
{
	va_list vl;

	test->conclusion = tc_passed;
	test->failure = tf_none;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = 0;
	test->operands[1] = 0;

	va_start(vl, format);
	vasprintf((char **) &test->report, format, vl);
	va_end(vl);
	asprintf((char **) &test->cause, "test->pass()");

	test->controls->exit(test);
	return(0);
}

#define _TCI_EXIT() \
	if (test->failure) \
		test->controls->exit(test); \
	return(rv);

#define _TCI_RETURN_OR_FAIL(CONDITION, NOP, ...) \
	do { \
		bool absurdity = CONDITION; \
		if (absurdity) op = NOP; \
		testr = _test_representation(test->contention_delta); \
		absurdity = _test_absurdity_control(test->contention_delta, absurdity); \
		test->contention_delta = ac_reflect; \
		if (absurdity) \
		{ \
			if (test->contention_trace) \
				test->contention_trace = false; \
			h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments); \
		} \
		else \
		{ \
			if (test->contention_trace) \
				test->contention_trace = false; \
			else \
			{ \
				__VA_ARGS__; \
				return(rv); \
			} \
		} \
	} while(0)

static inline int
_tci_contend_memcmp(_test_control_parameters, void *solution, void *candidate, size_t n)
{
	const char *testr = "test";
	const char *op = "==";
	int rv;

	++test->contentions;

	rv = (memcmp)(solution, candidate, n);
	_TCI_RETURN_OR_FAIL((rv != 0), "!=");

	_h_print_note(test,
		_h_cause("%s->memcmp(%s, %s, %zd) (returned %d)", testr, former, latter, n, rv),
		_h_report("\"%.*s\" %s \"%.*s\"", n, solution, op, n, candidate)
	);

	_TCI_EXIT();
}

static inline void *
_tci_contend_memchr(_test_control_parameters, void *solution, int candidate, size_t n)
{
	const char *testr = "test";
	const char *op = "was found (offset %zu) in";
	void *rv;
	intptr_t ri;

	++test->contentions;

	rv = (memchr)(solution, candidate, n);
	ri = (intptr_t) rv;
	_TCI_RETURN_OR_FAIL((rv == NULL), "not found in");

	{
		char opbuf[64];
		if (rv != NULL)
			snprintf(opbuf, sizeof(opbuf), op, (size_t) (ri - (intptr_t) solution));
		else
			snprintf(opbuf, sizeof(opbuf), op);

		_h_print_note(test,
			_h_cause("%s->memchr(%s, %s, %zu)", testr, former, latter, n),
			_h_report("'%c' (0x%X) %s %p (%zu bytes)",
				(unsigned char) candidate, candidate, opbuf, solution, n)
		);
	}

	_TCI_EXIT();
}

static inline void *
_tci_contend_memrchr(_test_control_parameters, void *solution, int candidate, size_t n)
{
	const char *testr = "test";
	const char *op = "was found (offset %zu) in";
	void *rv;
	intptr_t ri;

	++test->contentions;

	rv = (memrchr)(solution, candidate, n);
	ri = (intptr_t) rv;
	_TCI_RETURN_OR_FAIL((rv == NULL), "not found in");

	{
		char opbuf[64];
		if (rv != NULL)
			snprintf(opbuf, sizeof(opbuf), op, (size_t) (ri - (intptr_t) solution));
		else
			snprintf(opbuf, sizeof(opbuf), op);

		_h_print_note(test,
			_h_cause("%s->memrchr(%s, %s, %zu)", testr, former, latter, n),
			_h_report("'%c' (0x%X) %s %p (%zu bytes)",
				(unsigned char) candidate, candidate, opbuf, solution, n)
		);
	}

	_TCI_EXIT();
}

static inline int
_tci_contend_strcmpf(_test_control_parameters, const char *solution, const char *candidate, ...)
{
	const char *testr = "test";
	const char *op = "==";
	char *formatted = NULL;
	int rv, size;

	++test->contentions;

	{
		va_list args;
		va_start(args, candidate);
		size = vasprintf(&formatted, candidate, args);
		va_end(args);
	}

	rv = (strcmp)(solution, formatted);
	_TCI_RETURN_OR_FAIL((rv != 0), "!=", free((void *) formatted));

	_h_print_note(test,
		_h_cause("%s->strcmpf" "(%s, %s)", testr, former, latter),
		_h_report("\"%s\" %s \"%s\"", solution, op, formatted)
	);

	free((void *) formatted);
	_TCI_EXIT();
}

#define _TEST_CONTEND_STRINGS(TYPE, CHECK, CTYPE, CFORMAT, METHOD, OPSTR, NOPSTR) \
	static inline TYPE \
	_tci_contend_##METHOD(_test_control_parameters, CTYPE solution, CTYPE candidate) \
	{ \
		const char *testr = "test"; \
		const char *op = OPSTR; \
		TYPE rv; \
		++test->contentions; \
		\
		rv = (TYPE) (METHOD)(solution, candidate); \
		_TCI_RETURN_OR_FAIL(!CHECK(rv), NOPSTR); \
		\
		_h_print_note(test, \
			_h_cause("%s->" #METHOD "(%s, %s)", testr, former, latter), \
			_h_report("\"%" CFORMAT "\" %s \"%" CFORMAT "\"", solution, op, candidate) \
		); \
		\
		_TCI_EXIT(); \
	}

#define _TEST_CMP_CHECK(X) (X == 0)
#define _TEST_SEARCH_CHECK(X) (X != NULL)
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const char *, "s", strcmp, "==", "!=")
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const char *, "s", strcasecmp, "==", "!=")
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const wchar_t *, "ls", wcscmp, "==", "!=")
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const wchar_t *, "ls", wcscasecmp, "==", "!=")
	_TEST_CONTEND_STRINGS(char *, _TEST_SEARCH_CHECK, const char *, "s", strstr, "~", "!~")
	_TEST_CONTEND_STRINGS(char *, _TEST_SEARCH_CHECK, const char *, "s", strcasestr, "~", "!~")
	_TEST_CONTEND_STRINGS(wchar_t *, _TEST_SEARCH_CHECK, const wchar_t *, "ls", wcsstr, "~", "!~")
#undef _TEST_CMP_CHECK
#undef _TEST_SEARCH_CHECK

static inline int
_tci_contend_equality(_test_control_parameters, _test_format_parameters, intmax_t solution, intmax_t candidate)
{
	const char *testr = "test";
	const char *op = "==";
	int rv;
	++test->contentions;

	rv = (solution == candidate);
	_TCI_RETURN_OR_FAIL((!rv), "!=");

	{
		char fmt[64] = {0,};
		snprintf(fmt, sizeof(fmt), "%%%s %s %%%s", fofmt, op, lofmt);

		_h_print_note(test,
			_h_cause("%s->equality(%s, %s)", testr, former, latter),
			_h_report(fmt, solution, candidate)
		);
	}

	_TCI_EXIT();
}

static inline int
_tci_contend_truth(_test_control_parameters, intmax_t solution, intmax_t candidate)
{
	const char *testr = "test";
	const char *op = "+";
	int rv;
	++test->contentions;

	rv = solution;
	_TCI_RETURN_OR_FAIL((!rv), "-");

	_h_print_note(test,
		_h_cause("%s->truth(%s)", testr, former),
		_h_report("%s", rv ? "true" : "false")
	);

	_TCI_EXIT();
}

#if defined(TEST_SUITE_EXTENSION)
	#define TEST_DISABLE_MAIN test-suite-extension
#else
	sigjmp_buf _h_exit_root;
	struct HarnessTestRecord _h_function_zero = {0,};
	struct HarnessTestRecord *_h_function_index = &_h_function_zero;
	const char *_h_tmpdir_restriction = NULL;
	const char *_h_tmpdir_root = NULL;
#endif

#if !defined(TEST_SUITE_EXTENSION) || defined(_TEST_HARNESS_FUNCTIONS)
	static int
	h_sequential_exit(struct Test *t)
	{
		siglongjmp(_h_exit_root, 1);
		return(-1);
	}

	static int
	h_process_exit(struct Test *t)
	{
		exit((t->conclusion + 1) << 2 | t->failure);
		return(-1);
	}

	static int
	h_configure_tmpdir(int stf_receiver, stf_string_t suite, const char *fs_tmpdir_default)
	{
		setenv("TMPDIR", fs_tmpdir_default, 0);

		_h_tmpdir_root = getenv("TMPDIR");
		if (_h_tmpdir_root == NULL)
		{
			_h_tmpdir_restriction =
				"TMPDIR environment was not set after default configuration.";

			ttyn1_log_warning(stf_receiver, NULL, suite,
				TTYN_SYNOPSIS(
					"the TMPDIR environment variable was not available; "
					"`test->fs_tmp()` calls will conclude failure."),
				TTYN_EXTENSION()
			);

			errno = 0;
			return(0);
		}

		// Absolute restriction.
		if (_h_tmpdir_root[0] != '/')
		{
			_h_tmpdir_restriction = "TMPDIR is not an absolute path";

			ttyn1_log_warning(stf_receiver, NULL, suite,
				TTYN_SYNOPSIS(
					"temporary directory root (TMPDIR) must be absolute; "
					"`test->fs_tmp()` calls will conclude failure."),
				TTYN_EXTENSION(TTYN_INSERT_OPTION("path", (stf_string_t) _h_tmpdir_root))
			);
		}

		return(0);
	}

	/**
		// It is, arguably, inappropriate to clean up the temporary directory within
		// the same process as the test may have corrupted the path string or faulted
		// such that cleanup was not possible.
	*/
	static void
	h_cleanup_tmpdir(struct Test *t, bool wait)
	{
		const char *const xid = t->identity->ti_symbol;
		const char *const tmp = t->tmpdir_path;
		pid_t rmp = 0;

		#define warn(...) \
			ttyn1_log_warning(t->stf_receiver, NULL, xid, \
				TTYN_SYNOPSIS(__VA_ARGS__), \
				TTYN_EXTENSION( \
					TTYN_INSERT_OPTION("path", (stf_string_t) tmp) \
				) \
			)

		if (_h_hash_string(tmp) != t->tmpdir_path_hash)
		{
			// Protecting against memory corruption. Testing C programs here,
			// so try to make sure the rm -rf is (very) likely to be deleting the
			// temporary directory that was originally created.

			warn("temporary directory path string hash does not match "
				"and will not be removed due to likely memory corruption.");
			return;
		}

		if (strncmp(_h_tmpdir_root, tmp, strlen(_h_tmpdir_root)) != 0)
		{
			// Branch for intentional tmpdir leaks.
			// In cases where analysis of some (temporary) filesystem data
			// is desired, allow the test to configure the directory outside
			// of TMPDIR and ignore cleanup when the case is seen.

			warn("the allocated temporary directory is outside of "
				"the designated prefix (TMPDIR) and will not be removed.");
			return;
		}

		if (rmdir(tmp) == 0)
		{
			// Don't bother with the spawn if it's just a directory.
			return;
		}
		else
		{
			// Leverage the error case to perform additional safeties.
			int err = errno;
			errno = 0;

			switch (err)
			{
				case EPERM:
				case EACCES:
				{
					warn("temporary directory is not seen as writable "
						"and will not be removed.");
					return;
				}
				break;

				case ENOTDIR:
				{
					// Was not created by fs_tmp().
					warn("temporary directory path does not refer to a directory "
						"and will not be removed.");
					return;
				}

				case ENOENT:
					// Already removed?
					warn("temporary directory was removed prior to cleanup.");
					return;
				break;
			}
		}

		errno = 0;
		rmp = fork();
		switch (rmp)
		{
			#define cleanup_w(F) \
				"could not execute cleanup procedure; " \
				F " returned error (%d) status: %s"
			case 0:
			{
				// Utility fork process reaped by init.
				char *const argv[] = {TEST_FS_RM_PATH, "-rf", t->tmpdir_path, NULL};

				execve(argv[0], argv, NULL);
				warn(cleanup_w("execve"), (int) errno, strerror(errno));

				// Avoid normal exit procedures under a failed execve.
				_exit(256);
			}
			break;

			case -1:
			{
				// Test process. Could not fork.
				if (errno != 0)
					warn(cleanup_w("fork"), (int) errno, strerror(errno));
			}
			break;

			default:
			{
				// Test Process, fork() successful.
				if (wait)
				{
					int status = 0;
					waitpid(rmp, &status, 0);
				}
			}
			break;

			#undef cleanup_w
		}

		#undef warn
	}

	static inline size_t
	_harness_indent(const char **ref)
	{
		const char *txt = *ref;
		size_t len;
		if (txt == NULL)
			return(0);

		len = stf_indent_text((uint8_t **) ref,
			(stf_string_t) txt, strlen(txt), 8, 1);
		free((void *) txt);

		return(len);
	}

	/**
		// Execute a single test within the current process.
	*/
	static enum TestConclusion
	harness_test(int stf_receiver, const char *suite, int *contentions, struct TestControls *ctl, struct HarnessTestRecord *current)
	{
		struct Test ts;
		struct Test *t = &ts;
		struct rusage tu_before, tu_after;
		uint64_t start, stop;
		char duration[21];
		size_t report_len = 0, cause_len = 0;
		const char *tcstr;
		stf_metrics_t psm = {{0,0,0,0,.w_prepared=1},{0,},{0,}};

		t->controls = &(t->_controls);
		memcpy(t->controls, ctl, sizeof(struct TestControls));

		t->identity = current->htr_identity;
		t->conclusion = tc_skipped;
		t->contention_delta = ac_reflect;
		t->contention_trace = false;
		t->failure = tf_none;
		t->contentions = 0;

		t->tmpdir_path = NULL;
		t->tmpdir_path_hash = 0;

		t->stf_receiver = stf_receiver;
		t->source_line_number = t->identity->ti_line;
		t->source_path = t->identity->ti_source;
		t->function_name = t->identity->ti_symbol;
		t->operands[0] = "<>";
		t->operands[1] = "<>";

		t->cause = NULL;
		t->report = NULL;

		ttyn1_log_open_transaction(t->stf_receiver, NULL,
			(stf_string_t) t->identity->ti_symbol, &psm,
			TTYN_SYNOPSIS("%s/%s: dispatched", suite, t->identity->ti_symbol),
			TTYN_EXTENSION()
		);
		psm.ps_work.w_prepared = 0;

		getrusage(RUSAGE_SELF, &tu_before);
		start = STF_CLOCK_ELAPSED();

		if (sigsetjmp(_h_exit_root, 1))
		{
			stop = STF_CLOCK_ELAPSED();
			getrusage(RUSAGE_SELF, &tu_after);
			snprintf(duration, sizeof(duration), "%" PRIu64, stop - start);

			// Test exited; control method should have filled in conclusion.
			switch (t->conclusion)
			{
				case tc_skipped:
					tcstr = "skipped";
					psm.ps_work.w_granted = 1;
				break;

				case tc_failed:
					tcstr = "failed";
					psm.ps_work.w_failed = 1;
				break;

				case tc_passed:
					tcstr = "passed";
					psm.ps_work.w_executed = 1;
				break;
			}
		}
		else
		{
			current->htr_pointer(t);

			stop = STF_CLOCK_ELAPSED();
			getrusage(RUSAGE_SELF, &tu_after);
			snprintf(duration, sizeof(duration), "%" PRIu64, stop - start);

			// Only passed from returns.
			t->conclusion = tc_passed;
			tcstr = "passed";
			psm.ps_work.w_executed = 1;
		}

		cause_len = _harness_indent(&t->cause);
		report_len = _harness_indent(&t->report);

		psm.ps_usage.r_divisions = 1;
		psm.ps_usage.r_process = 1000000000 * (
			(tu_after.ru_utime.tv_sec + tu_after.ru_stime.tv_sec) -
			(tu_before.ru_utime.tv_sec + tu_before.ru_stime.tv_sec));
		psm.ps_usage.r_process += 1000 * (
			(tu_after.ru_utime.tv_usec + tu_after.ru_stime.tv_usec) -
			(tu_before.ru_utime.tv_usec + tu_before.ru_stime.tv_usec));
		psm.ps_usage.r_time = 0;

		// Useless with sequential dispatch.
		psm.ps_usage.r_memory = tu_after.ru_maxrss - tu_before.ru_maxrss;

		switch (t->failure)
		{
			case tf_none:
				if (t->report)
					ttyn1_log_close_transaction(t->stf_receiver, NULL,
						(stf_string_t) t->identity->ti_symbol, &psm,
						TTYN_SYNOPSIS("%s/%s: %s", suite, t->identity->ti_symbol, tcstr),
						TTYN_EXTENSION(
							TTYN_INSERT_OPTION("@duration", (uint8_t *) duration),

							TTYN_INSERT_SECTION("@operation", "test-contention"),
							_h_insert_location(t->source_path, t->source_line_number),
							TTYN_INSERT_NEWLINE,

							TTYN_INSERT_SECTION("@report", "test-summary"),
							TTYN_INSERT(report_len, t->report),
							TTYN_INSERT_NEWLINE
						)
					);
				else
					ttyn1_log_close_transaction(t->stf_receiver, NULL,
						(stf_string_t) t->identity->ti_symbol, &psm,
						TTYN_SYNOPSIS("%s/%s: %s", suite, t->identity->ti_symbol, tcstr),
						TTYN_EXTENSION(
							TTYN_INSERT_OPTION("@duration", (uint8_t *) duration)
						)
					);
			break;

			default:
				ttyn1_log_close_transaction(t->stf_receiver, NULL,
					(stf_string_t) t->identity->ti_symbol, &psm,
					TTYN_SYNOPSIS("%s/%s: %s", suite, t->identity->ti_symbol, tcstr),
					TTYN_EXTENSION(
						TTYN_INSERT_OPTION("@duration", (uint8_t *) duration),

						TTYN_INSERT_SECTION("@operation", "test-contention"),
						TTYN_INSERT(cause_len, t->cause),
						TTYN_INSERT_NEWLINE,

						_h_insert_location(t->source_path, t->source_line_number),
						TTYN_INSERT_NEWLINE,

						TTYN_INSERT_SECTION("@failure-image", "absurdity"),
						TTYN_INSERT(report_len, t->report),
						TTYN_INSERT_NEWLINE
					)
				);
			break;
		}

		if (t->tmpdir_path != NULL)
		{
			h_cleanup_tmpdir(t, false);

			free((void *) t->tmpdir_path);
			t->tmpdir_path = NULL;
			t->tmpdir_path_hash = 0;
		}

		if (t->cause)
			free((void *) t->cause);
		if (t->report)
			free((void *) t->report);

		*contentions += t->contentions;
		return(t->conclusion);
	}

	/**
		// Execute the tests.
	*/
	static int
	harness_execute_tests(int stf_receiver, const char *suite, TestDispatch htest, TestExit hexit)
	{
		#define _TCM_INIT(CTX, METHOD, STYPE, FTYPE) STYPE(METHOD),
		const struct TestControls default_controls = {
			TEST_CONTROL_METHODS(void, _TCM_INIT)
			_tci_fs_tmp,
			hexit
		};
		#undef _TCM_INIT

		struct HarnessTestRecord * const root = &_h_function_zero;
		struct HarnessTestRecord *current;
		int total = 0, test_count = 0, contentions = 0;
		int passed = 0, failed = 0, skipped = 0;

		current = root->next;
		while (current != NULL)
		{
			++total;
			current = current->next;
		}

		ttyn1_log_declaration(stf_receiver, NULL, suite);
		ttyn1_log_open_transaction(stf_receiver, NULL, suite,
			NULL,
			TTYN_SYNOPSIS("%s: harness selected %d tests for analysis.", suite, total),
			TTYN_EXTENSION()
		);

		h_configure_tmpdir(stf_receiver, (stf_string_t) suite, TEST_FS_TMPDIR_ROOT);

		current = root->next;
		while (current != NULL)
		{
			enum TestConclusion tc;
			tc = htest(stf_receiver, suite, &contentions,
				(struct TestControls *) &default_controls, current);

			test_count += 1;

			switch (tc)
			{
				case tc_failed:
					failed += 1;
				break;

				case tc_skipped:
					skipped += 1;
				break;

				case tc_passed:
					passed += 1;
				break;
			}

			current = current->next;
		}

		ttyn1_log_close_transaction(stf_receiver, NULL, suite, NULL,
			TTYN_SYNOPSIS(
				"%s: %u contentions across %u tests; "
				"%u failed, %u skipped, %u passed",
				suite, contentions, test_count, failed, skipped, passed),
			TTYN_EXTENSION()
		);
		return(0);
	}
#endif

#if !defined(TEST_DISABLE_MAIN)
	int
	main(int argc, char *argv[])
	{
		enum TestDispatchStrategy tdm = td_sequential;
		TestDispatch hdispatch = NULL;
		TestExit hexit = NULL;

		#if defined(TEST_SUITE_IDENTITY)
			const char *suite = TEST_SUITE_IDENTITY;
		#elif defined(FACTOR_PATH_STR)
			const char *suite = F_PROJECT_PATH_STR "/" F_FACTOR_STR;
		#else
			const char *suite = argv[0];
		#endif

		switch (tdm)
		{
			case td_sequential:
				hdispatch = harness_test;
				hexit = h_sequential_exit;
			break;
		}

		return(harness_execute_tests(TEST_STATUS_FRAME_RECEIVER, suite, hdispatch, hexit));
	}
#endif
#endif
