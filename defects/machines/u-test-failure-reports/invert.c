/**
	// Evaluate inverted contentions.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

#define note_failed_exit() fprintf(stderr, "CRITICAL: test did not exit after contending absurdity\n")

Test(failed_not_strcmpf)
{
	test(!)->strcmpf("test 10 'sub' string", "test %d '%s' string", 10, "sub");
	note_failed_exit();
}

Test(failed_not_truth)
{
	test(!)->truth(true);
	note_failed_exit();
}

Test(failed_not_memcmp)
{
	test(!)->memcmp("former", "former", 6);
	note_failed_exit();
}

Test(failed_not_memchr)
{
	test(!)->memchr("former", 'r', 6);
	note_failed_exit();
}

Test(failed_not_memrchr)
{
	test(!)->memrchr("former", 'f', 6);
	note_failed_exit();
}

Test(failed_not_strcmp)
{
	test(!)->strcmp("fail", "fail");
	note_failed_exit();
}

Test(failed_not_strcasecmp)
{
	test(!)->strcasecmp("fail", "FAIL");
	note_failed_exit();
}

Test(failed_not_wcscmp)
{
	test(!)->wcscmp(L"fail", L"fail");
	note_failed_exit();
}

Test(failed_not_wcscasecmp)
{
	test(!)->wcscasecmp(L"failed", L"FAILED");
	note_failed_exit();
}

Test(failed_not_wcsstr)
{
	test(!)->wcsstr(L"haystack of nothing", L"nothing");
	note_failed_exit();
}

Test(failed_not_strstr)
{
	test(!)->strstr("haystack of nothing", "nothing");
	note_failed_exit();
}

Test(failed_not_strcasestr)
{
	test(!)->strcasestr("haystack of nothing", "nothing");
	note_failed_exit();
}

Test(failed_not_equality)
{
	test(!)->equality(0, 0);
	note_failed_exit();
}
