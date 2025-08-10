/**
	// Contend and Conclude Test Protocol implementation for C.

	// [ Usage ]

	// #!syntax/c
		#include <fault/test.h>

		Test(feature)
		{
			if (feature_available == false)
				test->skip("feature not available");

			test->equality(10, 10);
			test->truth(function() == 100);
			test->strcmp("IdNameString", lookup_name(id));
			test->strstr("haystack of needles", "needle");
		}

	// If multiple sources are being compiled into the same target, the
	// `TEST_SUITE_EXTENSION` define should be set in all but one source
	// file that includes `test.h`:

	// #!syntax/c
		#define TEST_SUITE_EXTENSION
		#include <fault/test.h>

		Test(alternative)
		{
			test->fail()
		}

	// [ Test Control Methods ]

	// /`test->equality(intmax_t, intmax_t)`/
		// Fail when integers are not equal.

	// /`test->inequality(intmax_t, intmax_t)`/
		// Fail when integers are equal.

	// /`test->truth(int)`/
		// Fail when zero.

	// /`test->strcmpf(const char *solution, const char *format, ...)`/
		// Fail when the formatted string is not equal to the solution.

	// /`test->strcmp(const char *, const char *)`/
		// Fail when the strings are not equal.

	// /`test->strcasecmp(const char *, const char *)`/
		// Fail when, case insensitive, strings are not equal.

	// /`test->wcscmp(const wchar_t *, const wchar_t *)`/
		// Fail when strings are not equal.

	// /`test->wcscasecmp(const wchar_t *, const wchar_t *)`/
		// Fail when, case insensitive, strings are not equal.

	// /`test->strstr(const char *haystack, const char *needle)`/
		// Fail when the needle string is not found in haystack.

	// /`test->strcasestr(const char *haystack, const char *needle)`/
		// Fail when the, case insensitive, needle is not found in haystack.

	// /`test->wcsstr(const char *haystack, const char *needle)`/
		// Fail when the, wide character, needle is not found in haystack.

	// /`test->memcmp(void *, void *, size_t)`/
		// Fail when the bytes of memory references are not equal.

	// /`test->memchr(void *memory, int byte, size_t memory_size)`/
		// Fail when the byte could not be found in memory.

	// /`test->memrchr(void *memory, int byte, size_t memory_size)`/
		// Fail when the byte could not be found in memory with the
		// search starting at the end.

	// [ Integration Control Defines ]

	// /`TEST_SUITE_IDENTITY`/
		// String identifying the set of tests.
	// /`TEST_SUITE_EXTENSION`/
		// Definition used to signal the (test.h) header that the source should not
		// define global storage variables or the main function.

		// When compiling multiple sources, all but one source file should define this.
		// Given a common enough pattern, giving `-DTEST_SUITE_EXTENSION` to all sources
		// and using `#undef` in the main source file would be reasonable.

		// Alternatively, the main source file could include the extensions instead.

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
*/
#ifndef _FAULT_TEST_H_
#define _FAULT_TEST_H_

#ifndef h_printf
	#define h_printf(...) fprintf(stderr, __VA_ARGS__)
#endif
#ifndef h_vprintf
	#define h_vprintf(...) vfprintf(stderr, __VA_ARGS__)
#endif

#if !defined(TEST_DISABLE_DEFAULT_INCLUDES)
	#include <stdio.h>
	#include <stdarg.h>
	#include <string.h>
	#include <setjmp.h>
	#include <stdlib.h>
	#include <stdbool.h>
	#include <unistd.h>
	#include <inttypes.h>
	#include <wchar.h>
#endif

#if defined(__APPLE__) && !defined(TEST_DISABLE_LOCAL_MEMRCHR)
	// Not found in recent macOS versions.
	static inline void *
	memrchr(const void *memory, int c, size_t s)
	{
		const char *bytes = memory + s;
		const char b = c;

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

	// /tdm_sequential/
		// One test at a time in a single process.
		// &siglongjmp is used to exit concluded tests.
	// /tdm_thread/
		// Dispatch all tests concurrently in a single process.
		// &pthread_exit is used to exit tests.
	// /tdm_process/
		// Dispatch all tests concurrenctly using fork.
		// &exit is used to exit tests.
*/
enum TestDispatchMethod {
	tdm_sequential,
	tdm_thread,
	tdm_process
};

/**
	// Identifying information about the test.

	// [ Elements ]
	// /ti_name/
		// The base name of the test.
	// /ti_source/
		// The file that the test was defined in.
	// /ti_line/
		// The line number of the test's declaration.
	// /ti_index/
		// The __COUNTER__ value when the test was declared.
*/
struct TestIdentity {
	const char *ti_name;
	const char *ti_source;
	int ti_line;
	int ti_index;
};

/**
	// Test conclusions.

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
	tc_failed = -1,
	tc_skipped = 0,
	tc_passed = +1,
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
		// Failure was due to a system or application fault.
		// Language exceptions, segmentation violations, or anything that
		// may cause a test process to exit.
*/
enum FailureType {
	tf_limit = -3,
	tf_interrupt = -2,
	tf_explicit = -1,
	tf_none = 0,
	tf_absurdity = 1,
	tf_fault,
};

/**
	// Argument lists providing access to parameter names.
*/
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
#define _MEMCMP_T(FT) FT(_FTA_BINARY_1L, int, const void *solution, const void *candidate, size_t length)
#define _MEMCHR_T(FT) FT(_FTA_BINARY_1L, void *, const void *solution, int candidate, size_t length)
#define _LSTRSTR_T(FT) FT(_FTA_BINARY, wchar_t *, const wchar_t *solution, const wchar_t *candidate)
#define _LSTRCMP_T(FT) FT(_FTA_BINARY, int, const wchar_t *solution, const wchar_t *candidate)

#define _LOG_SF(SYMBOL) _tci_##SYMBOL##_test
#define _CONTEND_SF(SYMBOL) _tci_contend_##SYMBOL

#define _ECHO(...) __VA_ARGS__
#define _WRAP(...) (__VA_ARGS__)

#define TEST_CONTROL_METHODS(CONTEXT, TM) \
	TM(CONTEXT, fail, _LOG_SF, _LOG_T) \
	TM(CONTEXT, skip, _LOG_SF, _LOG_T) \
	TM(CONTEXT, pass, _LOG_SF, _LOG_T) \
	TM(CONTEXT, truth, _CONTEND_SF, _INTCMP_T) \
	TM(CONTEXT, equality, _CONTEND_SF, _INTCMPF_T) \
	TM(CONTEXT, inequality, _CONTEND_SF, _INTCMPF_T) \
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
#define _test_control_parameters \
	struct Test *test, _location_parameters, _test_control_operand_parameters
#define _test_format_arguments opstr, fofmt, lofmt
#define _test_format_parameters const char *opstr, const char *fofmt, const char *lofmt

struct Test;
struct TestControls {
	#define TEST_METHOD_DECLARATIONS(CTX, METHOD, STYPE, FTYPE) \
		FTYPE(_FT_RETURN) (* METHOD)(_test_control_parameters, FTYPE(_FT_PARAMETERS));

		TEST_CONTROL_METHODS(void, TEST_METHOD_DECLARATIONS)
	#undef TEST_METHOD_DECLARATIONS

	int (*exit)(struct Test *);
};

struct Test {
	// Keeping the test controls allocation with the start of Test to
	// minimize the difficulty of aligning compatible methods.
	struct TestControls _controls;
	struct TestControls *controls;

	// Provided by the HarnessTestRecord
	struct TestIdentity *identity;

	// Exposed, but only used by control methods.
	uint64_t contentions;
	enum TestConclusion conclusion:4;
	enum FailureType failure:4;

	// As recognized by the control macros.
	// Filled when a test is concluded.
	const char *source_path;
	uint32_t source_line_number;
	const char *function_name;
	const char *operands[2];
};

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
	{ return((FNAME)(FTYPE(_FT_ARGUMENTS))); }

TEST_CONTROL_PROXIES(DEFINE_PROXY)
#undef DEFINE_PROXY

const static struct TestControls _tif_ctlgad = {
	#define PINIT(NAME, TYPE) .NAME = _##NAME##_proxy,
		TEST_CONTROL_PROXIES(PINIT)
	#undef PINIT
};
const static struct Test _tif_tgad = {&_tif_ctlgad,};

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
	(int *, struct TestControls *, struct HarnessTestRecord *);
typedef int (*TestExit)(struct Test *);

// Sequential single process dispatch uses this to exit tests upon concluding.
extern sigjmp_buf _h_exit_root;
extern struct HarnessTestRecord _h_function_zero;
extern struct HarnessTestRecord *_h_function_index;

#define _TEST_RECORD_CONSTRUCTOR(NAME, FILE, LINE, INDEX) \
	static void __attribute__((constructor)) _h_##NAME##_add(void) { \
		struct HarnessTestRecord *tfr; \
		struct TestIdentity *ti; \
		\
		tfr = malloc(sizeof(struct HarnessTestRecord)); \
		if (tfr == NULL) abort(); \
		ti = malloc(sizeof(struct TestIdentity)); \
		if (ti == NULL) abort(); \
		\
		ti->ti_name = #NAME; \
		ti->ti_source = FILE; \
		ti->ti_line = LINE; \
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
	void NAME (struct Test *test)

#ifdef __COUNTER__
	#define _Test(NAME, INDEX, ...) \
		_TEST_FUNCTION_DECLARATION(test_##NAME); \
		_TEST_RECORD_CONSTRUCTOR(NAME, __FILE__, __LINE__, INDEX) \
		_TEST_FUNCTION_DECLARATION(test_##NAME)
	#define Test(NAME, ...) _Test(NAME, __COUNTER__, __VA_ARGS__)
#else
	#error "__COUNTER__ macro is required."
#endif

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
	ISOLATION(TEST_CONTROLS->METHOD)(_test_control_macro_arguments, __VA_ARGS__)

#define _TEST_METHOD_FAIL(S, CTL, ...) _TEST_MACRO_DIRECTION(S, CTL, fail, "void", "void", __VA_ARGS__)
#define _TEST_METHOD_SKIP(S, CTL, ...) _TEST_MACRO_DIRECTION(S, CTL, skip, "void", "void", __VA_ARGS__)
#define _TEST_METHOD_PASS(S, CTL, ...) _TEST_MACRO_DIRECTION(S, CTL, pass, "void", "void", __VA_ARGS__)

#define _TEST_METHOD_MEMCMP(S, CTL, A, B, SZ) _TEST_MACRO_DIRECTION(S, CTL, memcmp, #A, #B, A, B, SZ)
#define _TEST_METHOD_MEMCHR(S, CTL, A, B, SZ) _TEST_MACRO_DIRECTION(S, CTL, memchr, #A, #B, A, B, SZ)
#define _TEST_METHOD_MEMRCHR(S, CTL, A, B, SZ) _TEST_MACRO_DIRECTION(S, CTL, memrchr, #A, #B, A, B, SZ)

#define _TEST_METHOD_STRCMPF(S, CTL, A, B, ...) _TEST_MACRO_DIRECTION(S, CTL, strcmpf, #A, #B, A, B, __VA_ARGS__)
#define _TEST_METHOD_STRCMP(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, strcmp, #A, #B, A, B)
#define _TEST_METHOD_STRCASECMP(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, strcasecmp, #A, #B, A, B)
#define _TEST_METHOD_WCSCMP(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, wcscmp, #A, #B, A, B)
#define _TEST_METHOD_WCSCASECMP(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, wcscasecmp, #A, #B, A, B)
#define _TEST_METHOD_WCSSTR(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, wcsstr, #A, #B, A, B)
#define _TEST_METHOD_STRSTR(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, strstr, #A, #B, A, B)
#define _TEST_METHOD_STRCASESTR(S, CTL, A, B) _TEST_MACRO_DIRECTION(S, CTL, strcasestr, #A, #B, A, B)

#define _TEST_METHOD_EQUALITY(S, CTL, A, B) \
	_TEST_MACRO_DIRECTION(S, CTL, equality, #A, #B, _TEST_FORMATTING("!=", A, B), A, B)
#define _TEST_METHOD_INEQUALITY(S, CTL, A, B) \
	_TEST_MACRO_DIRECTION(S, CTL, inequality, #A, #B, _TEST_FORMATTING("==", A, B), A, B)
#define _TEST_METHOD_TRUTH(S, CTL, A, ...) _TEST_MACRO_DIRECTION(S, CTL, truth, #A, "void", A, 0)

#define test(...) (test->controls->truth)(_test_control_macro_arguments, #__VA_ARGS__, "void", __VA_ARGS__, 0)

/**
	// Namespace friendly test controls.
*/
#define fail_test(...) _TEST_METHOD_FAIL(_WRAP, test->controls, __VA_ARGS__)
#define skip_test(...) _TEST_METHOD_SKIP(_WRAP, test->controls, __VA_ARGS__)
#define pass_test(...) _TEST_METHOD_PASS(_WRAP, test->controls, __VA_ARGS__)

#define contend_truth(...) _TEST_METHOD_TRUTH(_WRAP, test->controls, __VA_ARGS__)
#define contend_equality(...) _TEST_METHOD_EQUALITY(_WRAP, test->controls, __VA_ARGS__)
#define contend_inequality(...) _TEST_METHOD_INEQUALITY(_WRAP, test->controls, __VA_ARGS__)

#define contend_memcmp(...) _TEST_METHOD_MEMCMP(_WRAP, test->controls, __VA_ARGS__)
#define contend_memchr(...) _TEST_METHOD_MEMCHR(_WRAP, test->controls, __VA_ARGS__)
#define contend_memrchr(...) _TEST_METHOD_MEMRCHR(_WRAP, test->controls, __VA_ARGS__)

#define contend_strstr(...) _TEST_METHOD_STRSTR(_WRAP, test->controls, __VA_ARGS__)
#define contend_strcasestr(...) _TEST_METHOD_STRCASESTR(_WRAP, test->controls, __VA_ARGS__)
#define contend_strcmp(...) _TEST_METHOD_STRCMP(_WRAP, test->controls, __VA_ARGS__)
#define contend_strcasecmp(...) _TEST_METHOD_STRCASECMP(_WRAP, test->controls, __VA_ARGS__)
#define contend_strcmpf(...) _TEST_METHOD_STRCMPF(_WRAP, test->controls, __VA_ARGS__)

#define contend_wcscmp(...) _TEST_METHOD_WCSCMP(_WRAP, test->controls, __VA_ARGS__)
#define contend_wcscasecmp(...) _TEST_METHOD_WCSCASECMP(_WRAP, test->controls, __VA_ARGS__)
#define contend_wcsstr(...) _TEST_METHOD_WCSSTR(_WRAP, test->controls, __VA_ARGS__)

/**
	// Invasive test controls that allow for a syntax that is compatible
	// with simple structure abstractions.
*/
#if !defined(TEST_DISABLE_INVASIVE_CONTROLS)
	#define fail(...) _TEST_METHOD_FAIL(_ECHO, controls, __VA_ARGS__)
	#define skip(...) _TEST_METHOD_SKIP(_ECHO, controls, __VA_ARGS__)
	#define pass(...) _TEST_METHOD_FAIL(_ECHO, controls, __VA_ARGS__)

	#define truth(...) _TEST_METHOD_TRUTH(_ECHO, controls, __VA_ARGS__)
	#define equality(...) _TEST_METHOD_EQUALITY(_ECHO, controls, __VA_ARGS__)
	#define inequality(...) _TEST_METHOD_INEQUALITY(_ECHO, controls, __VA_ARGS__)

	#define memcmp(...) _TEST_METHOD_MEMCMP(_ECHO, controls, __VA_ARGS__)
	#define memchr(...) _TEST_METHOD_MEMCHR(_ECHO, controls, __VA_ARGS__)
	#define memrchr(...) _TEST_METHOD_MEMRCHR(_ECHO, controls, __VA_ARGS__)

	#define strstr(...) _TEST_METHOD_STRSTR(_ECHO, controls, __VA_ARGS__)
	#define strcasestr(...) _TEST_METHOD_STRCASESTR(_ECHO, controls, __VA_ARGS__)
	#define strcmp(...) _TEST_METHOD_STRCMP(_ECHO, controls, __VA_ARGS__)
	#define strcasecmp(...) _TEST_METHOD_STRCASECMP(_ECHO, controls, __VA_ARGS__)
	#define strcmpf(...) _TEST_METHOD_STRCMPF(_ECHO, controls, __VA_ARGS__)

	#define wcscmp(...) _TEST_METHOD_WCSCMP(_ECHO, controls, __VA_ARGS__)
	#define wcscasecmp(...) _TEST_METHOD_WCSCASECMP(_ECHO, controls, __VA_ARGS__)
	#define wcsstr(...) _TEST_METHOD_WCSSTR(_ECHO, controls, __VA_ARGS__)
#endif

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

static inline void
h_print_location(struct Test *t)
{
	h_printf("\tLocation: line %d in \"%s\"\n", t->source_line_number, t->source_path);
}

static inline void
h_print_message(struct Test *t, char *message, va_list args)
{
	h_printf("\tMessage: ");
	h_vprintf(message, args);
	h_printf("\n");
}

static inline void
h_print_failure(struct Test *t)
{
	struct TestIdentity *ti = t->identity;
	h_printf("test_%s failed after %d contentions.\n", ti->ti_name, t->contentions);
}

#define h_absurdity(fmt, ...) h_printf("\tAbsurdity: " fmt "\n", __VA_ARGS__)
#define h_reality(fmt, ...) h_printf("\t" fmt "\n", __VA_ARGS__)
#define h_reality_variable(fmt, ...) h_printf(fmt, __VA_ARGS__)
#define h_inhibit(fmt, ...) do { ; } while(0)
#define h_note_failure(T, A, R) do { \
	h_print_failure(T); A; R; h_print_location(T); \
} while(0)
#define h_forward_va(format) { \
	va_list args; \
	va_start(args, format); \
	h_print_message(test, format, args); \
	va_end(args); \
}

static inline int
_tci_fail_test(_test_control_parameters, const char *format, ...)
{
	test->conclusion = tc_failed;
	test->failure = tf_explicit;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = 0;
	test->operands[1] = 0;

	h_print_failure(test);

	h_forward_va(format);

	h_print_location(test);
	test->controls->exit(test);
	return(0);
}

static inline int
_tci_skip_test(_test_control_parameters, const char *format, ...)
{
	test->conclusion = tc_skipped;
	test->failure = tf_none;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = 0;
	test->operands[1] = 0;

	test->controls->exit(test);
	return(0);
}

static inline int
_tci_pass_test(_test_control_parameters, const char *format, ...)
{
	test->conclusion = tc_passed;
	test->failure = tf_none;
	test->source_path = path;
	test->source_line_number = ln;
	test->function_name = fn;
	test->operands[0] = 0;
	test->operands[1] = 0;

	test->controls->exit(test);
	return(0);
}

static inline int
_tci_contend_memcmp(_test_control_parameters, const void *solution, const void *candidate, size_t n)
{
	++test->contentions;

	if ((memcmp)(solution, candidate, n) == 0)
		return(0);

	h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
	h_note_failure(test,
		h_absurdity("test->memcmp(%s, %s, %zd)", former, latter, n),
		h_reality("\"%.*s\" != \"%.*s\"", n, solution, n, candidate)
	);

	test->controls->exit(test);
	return(-1);
}

static inline void *
_tci_contend_memchr(_test_control_parameters, const void *solution, int candidate, size_t n)
{
	void *r;
	++test->contentions;

	r = (memchr)(solution, candidate, n);
	if (r != NULL)
		return(r);

	h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
	h_note_failure(test,
		h_absurdity("test->memchr(%s, %s, %zd)", former, latter, n),
		h_reality("0x%X not found in %p (%zu bytes)", candidate, solution, n)
	);

	test->controls->exit(test);
	return(NULL);
}

static inline void *
_tci_contend_memrchr(_test_control_parameters, const void *solution, int candidate, size_t n)
{
	void *r;
	++test->contentions;

	r = (memrchr)(solution, candidate, n);
	if (r != NULL)
		return(r);

	h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
	h_note_failure(test,
		h_absurdity("test->memrchr(%s, %s, %zd)", former, latter, n),
		h_reality("0x%X not found in %p (%zu bytes)", candidate, solution, n)
	);

	test->controls->exit(test);
	return(NULL);
}

static inline int
_tci_contend_strcmpf(_test_control_parameters, const char *solution, const char *candidate, ...)
{
	const char *formatted = NULL;
	int cr, size;
	++test->contentions;

	{
		va_list args;
		va_start(args, candidate);
		size = vasprintf(&formatted, candidate, args);
		va_end(args);
	}

	cr = (strcmp)(solution, formatted);
	if (cr == 0)
	{
		free(formatted);
		return(cr);
	}

	h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
	h_note_failure(test,
		h_absurdity("test->strcmpf" "(%s, %s)", former, latter),
		h_reality("\"%s\" != \"%s\"", solution, formatted)
	);

	free(formatted);
	test->controls->exit(test);
	return(-1);
}

#define _TEST_CONTEND_STRINGS(TYPE, CHECK, CTYPE, CFORMAT, METHOD, OPSTR) \
	static inline TYPE \
	_tci_contend_##METHOD(_test_control_parameters, CTYPE solution, CTYPE candidate) \
	{ \
		TYPE cr; \
		++test->contentions; \
		\
		cr = (METHOD)(solution, candidate); \
		if (CHECK(cr)) \
			return(cr); \
		\
		h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments); \
		h_note_failure(test, \
			h_absurdity("test->" #METHOD "(%s, %s)", former, latter), \
			h_reality("\"%" CFORMAT "\" " OPSTR " \"%" CFORMAT "\"", solution, candidate) \
		); \
		\
		test->controls->exit(test); \
		return(cr); \
	}

#define _TEST_CMP_CHECK(X) (X == 0)
#define _TEST_SEARCH_CHECK(X) (X != NULL)
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const char *, "s", strcmp, "!=")
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const char *, "s", strcasecmp, "!=")
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const wchar_t *, "ls", wcscmp, "!=")
	_TEST_CONTEND_STRINGS(int, _TEST_CMP_CHECK, const wchar_t *, "ls", wcscasecmp, "!=")
	_TEST_CONTEND_STRINGS(char *, _TEST_SEARCH_CHECK, const char *, "s", strstr, "!~")
	_TEST_CONTEND_STRINGS(char *, _TEST_SEARCH_CHECK, const char *, "s", strcasestr, "!~")
	_TEST_CONTEND_STRINGS(wchar_t *, _TEST_SEARCH_CHECK, const wchar_t *, "ls", wcsstr, "!~")
#undef _TEST_CMP_CHECK
#undef _TEST_SEARCH_CHECK

static inline int
_tci_contend_equality(_test_control_parameters, _test_format_parameters, intmax_t solution, intmax_t candidate)
{
	++test->contentions;

	if (solution == candidate)
		return(1);
	else
	{
		char fmt[16] = {0,};
		snprintf(fmt, sizeof(fmt), "\t%%%s %s %%%s\n", fofmt, opstr, lofmt);

		h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
		h_note_failure(test,
			h_absurdity("test->equality(%s, %s)", former, latter),
			h_reality_variable(fmt, solution, candidate)
		);
	}

	test->controls->exit(test);
	return(0);
}

static inline int
_tci_contend_inequality(_test_control_parameters, _test_format_parameters, intmax_t solution, intmax_t candidate)
{
	++test->contentions;

	if (solution != candidate)
		return(1);
	else
	{
		char fmt[16];
		snprintf(fmt, sizeof(fmt), "\t%%%s %s %%%s\n", fofmt, opstr, lofmt);

		h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
		h_note_failure(test,
			h_absurdity("test->inequality(%s, %s)", former, latter),
			h_reality_variable(fmt, solution, candidate)
		);
	}

	test->controls->exit(test);
	return(0);
}

static inline int
_tci_contend_truth(_test_control_parameters, intmax_t solution, intmax_t candidate)
{
	++test->contentions;

	if (solution)
		return(1);

	h_conclude_test(tc_failed, tf_absurdity, _test_control_arguments);
	h_note_failure(test,
		h_absurdity("test->truth(%s)", former),
		h_inhibit()
	);

	test->controls->exit(test);
	return(0);
}

#if defined(TEST_SUITE_EXTENSION)
	#define TEST_DISABLE_MAIN test-suite-extension
#else
	sigjmp_buf _h_exit_root;
	struct HarnessTestRecord _h_function_zero = {0,};
	struct HarnessTestRecord *_h_function_index = &_h_function_zero;

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

	/**
		// Execute a single test within the current process.
	*/
	enum TestConclusion
	harness_test(int *contentions, struct TestControls *ctl, struct HarnessTestRecord *current)
	{
		struct Test ts;
		struct Test *t = &ts;

		t->controls = &(t->_controls);
		memcpy(t->controls, ctl, sizeof(struct TestControls));

		t->identity = current->htr_identity;
		t->conclusion = tc_skipped;
		t->failure = 0;
		t->contentions = 0;

		t->source_line_number = t->identity->ti_line;
		t->source_path = t->identity->ti_source;
		t->function_name = t->identity->ti_name;
		t->operands[0] = "<>";
		t->operands[1] = "<>";

		if (sigsetjmp(_h_exit_root, 1))
		{
			// Test exited; control method should have filled in conclusion.
		}
		else
		{
			current->htr_pointer(t);
			t->conclusion = tc_passed;
		}

		*contentions += t->contentions;
		return(t->conclusion);
	}

	/**
		// Execute the tests.
	*/
	int
	harness_execute_tests(const char *suite, TestDispatch htest, TestExit hexit)
	{
		#define _TCM_INIT(CTX, METHOD, STYPE, FTYPE) STYPE(METHOD),
		const struct TestControls default_controls = {
			TEST_CONTROL_METHODS(void, _TCM_INIT)
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

		h_printf("%s: %d test records.\n", suite, total);

		current = root->next;
		while (current != NULL)
		{
			enum TestConclusion tc = htest(&contentions, &default_controls, current);

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

		h_printf("%d contentions across %d tests, %d passed, %d failed, %d skipped.\n",
			contentions, test_count, passed, failed, skipped);
		return(0);
	}
#endif

#if !defined(TEST_DISABLE_MAIN)
	int
	main(int argc, char *argv[])
	{
		enum TestDispatchMethod tdm = tdm_sequential;
		TestDispatch hdispatch = NULL;
		TestExit hexit = NULL;

		#if defined(TEST_SUITE_IDENTITY)
			const char *suite = TEST_SUITE_IDENTITY;
		#elif defined(FACTOR_PATH_STR)
			const char *suite = FACTOR_PATH_STR;
		#else
			const char *suite = argv[0];
		#endif

		switch (tdm)
		{
			case tdm_sequential:
				hdispatch = harness_test;
				hexit = h_sequential_exit;
			break;
		}

		return(harness_execute_tests(suite, hdispatch, hexit));
	}
#endif
#endif
