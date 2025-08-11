/**
	// Evaluate inverted contentions.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

Test(not_strcmpf)
{
	test(!)->strcmpf("test 10 'sub' string", "test %d '%s' string", -1, "sub");
}

Test(not_truth)
{
	test(!)->truth(0);
	test(!)->truth(!1);
}

Test(not_memcmp)
{
	test(!)->memcmp("former", "latter", 6);
}

Test(not_memchr)
{
	test(!)->memchr("former", 'z', 6);
}

Test(not_memrchr)
{
	test(!)->memrchr("former", 'z', 6);
}

Test(not_strcmp)
{
	test(!)->strcmp("Fail", "fail");
}

Test(not_strcasecmp)
{
	test(!)->strcasecmp("fai1", "FAIL");
}

Test(not_wcscmp)
{
	test(!)->wcscmp(L"FAIL", L"fail");
}

Test(not_wcscasecmp)
{
	test(!)->wcscasecmp(L"fai1ed", L"FAILED");
}

Test(not_wcsstr)
{
	test(!)->wcsstr(L"haystack of nothing", L"needle");
}

Test(not_strstr)
{
	test(!)->strstr("haystack of nothing", "needle");
}

Test(not_strcasestr)
{
	test(!)->strcasestr("haystack of nothing", "needle");
}

Test(not_equality)
{
	test(!)->equality(0, 1);
	test(!)->equality(-1, 1);
}
