/**
	// Validate Objective-C compatibility as primary source file.
*/
#include <fault/libc.h>

#include <fault/test.h>

#if __APPLE__
#import <Foundation/Foundation.h>

Test(objc_main_invocation)
{
	NSString *str = [NSString stringWithUTF8String: "test-string"];

	test->equality('t', [str characterAtIndex: 0]);
	test->equality('-', [str characterAtIndex: 4]);
}
#endif
