/**
	// Contend and Conclude Test Protocol implementation for C.

	// [ Usage ]

	// Aside from `equality`, `truth`, and a couple others, the default contentions are
	// named after their corresponding libc function and maintain their interface.

	// #!syntax/c
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

	// /`TEST_DISABLE_INVASIVE_CONTROLS`/
		// Disable many control macros providing test control context information
		// in cases of contended absurdities(C Preprocessor provided location information).
		// While `strcmp`, `strcasecmp`, and `memcmp` have resolution proxies so that they
		// may be used directly, methods like `pass`, `fail`, and `skip` could easily cause
		// conflicts without tangible resolutions as there are no standard forms to adapt to.
*/
#ifndef _FAULT_TEST_H_
#define _FAULT_TEST_H_
#define __HARNESS_INTERFACE__
	#include "intrinsics/harness.h"
#undef __HARNESS_INTERFACE__
#endif
