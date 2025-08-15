/**
	// Validate Objective-C under TEST_SUITE_EXTENSION.
*/
#include <fault/libc.h>

#define TEST_SUITE_EXTENSION
#include <fault/test.h>

#if __APPLE__
#import <Foundation/Foundation.h>

Test(objc_suite_extension)
{
	NSString *str = [NSString stringWithUTF8String: "test-string"];

	test->equality('t', [str characterAtIndex: 0]);
	test->equality('-', [str characterAtIndex: 4]);
}
#endif
