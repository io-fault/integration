/**
	// Evaluate always absurdity controls.

	// Check `test(-)` behavior with true contentions.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(failed_true_strcmpf)
{
	test(-)->strcmpf("test 10 'sub' string", "test %d '%s' string", 10, "sub");
	note_failed_exit();
}

Test(failed_true_truth)
{
	test(-)->truth(true);
	note_failed_exit();
}

Test(failed_true_memcmp)
{
	test(-)->memcmp("former", "former", 6);
	note_failed_exit();
}

Test(failed_true_memchr)
{
	test(-)->memchr("former", 'r', 6);
	note_failed_exit();
}

Test(failed_true_memrchr)
{
	test(-)->memrchr("former", 'f', 6);
	note_failed_exit();
}

Test(failed_true_strcmp)
{
	test(-)->strcmp("fail", "fail");
	note_failed_exit();
}

Test(failed_true_strcasecmp)
{
	test(-)->strcasecmp("fail", "FAIL");
	note_failed_exit();
}

Test(failed_true_wcscmp)
{
	test(-)->wcscmp(L"fail", L"fail");
	note_failed_exit();
}

Test(failed_true_wcscasecmp)
{
	test(-)->wcscasecmp(L"failed", L"FAILED");
	note_failed_exit();
}

Test(failed_true_wcsstr)
{
	test(-)->wcsstr(L"haystack of nothing", L"nothing");
	note_failed_exit();
}

Test(failed_true_strstr)
{
	test(-)->strstr("haystack of nothing", "nothing");
	note_failed_exit();
}

Test(failed_true_strcasestr)
{
	test(-)->strcasestr("haystack of nothing", "nothing");
	note_failed_exit();
}

Test(failed_true_equality)
{
	test(-)->equality(0, 0);
	note_failed_exit();
}
