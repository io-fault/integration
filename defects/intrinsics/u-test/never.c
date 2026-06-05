/**
	// Evaluate always failure absurdity controls.

	// The outer contentions validate that the inner test returns the expected status.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

Test(always_passed_equality)
{
	test(+test(+)->equality(+0, +0));
	test(+test(+)->equality(-1, -1));
	test(+test(+)->equality(+1, +1));
	test(!test(+)->equality(+1, +0));
	test(!test(+)->equality(+0, +1));
}

Test(always_passed_truth)
{
	test(+test(+)->truth(+true));
	test(!test(+)->truth(false));
}

Test(always_passed_strcmpf)
{
	test(test(+)->strcmpf("test 10 'sub' string", "test %d '%s' string", 10, "sub") == 0);
	test(test(+)->strcmpf("test 10 'sub' string", "test %d '%s' string", -1, "sub") != 0);
}

Test(always_passed_memcmp)
{
	test(test(+)->memcmp("former", "former", 6) == 0);
	test(test(+)->memcmp("former", "latter", 6) != 0);
}

Test(always_passed_memchr)
{
	test(test(+)->memchr("former", 'r', 6) != 0);
	test(test(+)->memchr("former", 'z', 6) == 0);
}

Test(always_passed_memrchr)
{
	test(test(+)->memrchr("former", 'f', 6) != 0);
	test(test(+)->memrchr("former", 'z', 6) == 0);
}

Test(always_passed_strcmp)
{
	test(test(+)->strcmp("fail", "fail") == 0);
	test(test(+)->strcmp("fail", "Fail") != 0);
	test(test(+)->strcmp("fail", "pass") != 0);
}

Test(always_passed_strcasecmp)
{
	test(test(+)->strcasecmp("fail", "FAIL") == 0);
	test(test(+)->strcasecmp("fail", "fail") == 0);
	test(test(+)->strcasecmp("fail", "pass") != 0);
}

Test(always_passed_wcscmp)
{
	test(test(+)->wcscmp(L"fail", L"fail") == 0);
	test(test(+)->wcscmp(L"fail", L"Fail") != 0);
	test(test(+)->wcscmp(L"fail", L"pass") != 0);
}

Test(always_passed_wcscasecmp)
{
	test(test(+)->wcscasecmp(L"failed", L"FAILED") == 0);
	test(test(+)->wcscasecmp(L"failed", L"failed") == 0);
	test(test(+)->wcscasecmp(L"failed", L"passed") != 0);
}

Test(always_passed_wcsstr)
{
	test(test(+)->wcsstr(L"haystack of nothing", L"nothing") != 0);
	test(test(+)->wcsstr(L"haystack of nothing", L"needles") == 0);
}

Test(always_passed_strstr)
{
	test(test(+)->strstr("haystack of nothing", "nothing") != 0);
	test(test(+)->strstr("haystack of nothing", "needles") == 0);
}

Test(always_passed_strcasestr)
{
	test(test(+)->strcasestr("haystack of nothing", "nothing") != 0);
	test(test(+)->strcasestr("haystack of nothing", "NOTHING") != 0);
	test(test(+)->strcasestr("haystack of nothing", "needles") == 0);
}
