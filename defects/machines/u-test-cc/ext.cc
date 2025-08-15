/**
	// Validate C++ compatibility under TEST_SUITE_EXTENSION.
*/
#include <iostream>
#include <vector>
#include <string>

#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

Test(cc_suite_extension)
{
	std::vector<std::string> ccv = {"s1", "s2", "s3"};
	ccv.push_back("s4");

	test->equality(4, ccv.size());
	test->strcmp(ccv[0].c_str(), "s1");
	test->strcmp(ccv[3].c_str(), "s4");
}
