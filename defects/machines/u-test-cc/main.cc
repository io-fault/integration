/**
	// Validate C++ compatibility as primary source file.
*/
#include <iostream>
#include <vector>
#include <string>

#include <fault/libc.h>
#include <fault/test.h>

Test(cc_main_invocation)
{
	std::vector<std::string> ccv = {"s1", "s2", "s3"};
	ccv.push_back("s4");

	test->equality(4, ccv.size());
	test->strcmp(ccv[0].c_str(), "s1");
	test->strcmp(ccv[3].c_str(), "s4");
}
