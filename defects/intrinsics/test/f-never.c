/**
	// Evaluate always absurd controls.

	// Check `test(-)` behavior with false contentions.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(failed_false_equality)
{
	test(-)->equality(0, 0);
	note_failed_exit();
}

Test(failed_false_strcmpf)
{
	test(-)->strcmpf("test 10 'sub' string", "test %d '%s' string", -1, "sub");
	note_failed_exit();
}

Test(failed_false_truth)
{
	test(-)->truth(false);
	note_failed_exit();
}

Test(failed_false_memcmp)
{
	test(-)->memcmp("former", "latter", 6);
	note_failed_exit();
}

Test(failed_false_memchr)
{
	test(-)->memchr("former", 'z', 6);
	note_failed_exit();
}

Test(failed_false_memrchr)
{
	test(-)->memrchr("former", 'z', 6);
	note_failed_exit();
}

Test(failed_false_strcmp)
{
	test(-)->strcmp("fail", "pass");
	note_failed_exit();
}

Test(failed_false_strcasecmp)
{
	test(-)->strcasecmp("fail", "pass");
	note_failed_exit();
}

Test(failed_false_wcscmp)
{
	test(-)->wcscmp(L"fail", L"pass");
	note_failed_exit();
}

Test(failed_false_wcscasecmp)
{
	test(-)->wcscasecmp(L"failed", L"passed");
	note_failed_exit();
}

Test(failed_false_wcsstr)
{
	test(-)->wcsstr(L"haystack of nothing", L"needle");
	note_failed_exit();
}

Test(failed_false_strstr)
{
	test(-)->strstr("haystack of nothing", "needle");
	note_failed_exit();
}

Test(failed_false_strcasestr)
{
	test(-)->strcasestr("haystack of nothing", "needle");
	note_failed_exit();
}
