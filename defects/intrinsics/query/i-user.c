/**
	// Validate user inquiries.
*/
#include <float.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <inttypes.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <pwd.h>
#include <fault/libc.h>
#include <fault/clock.h>
#include <fault/metrics.h>
#include <fault/test.h>
#include <fault/query.h>

Test(self_lookup)
{
	user_profile_t *u;

	u = user_profile(getuid());
	test(u != NULL);
	#ifdef __linux__
		test->strcmp("", u->u_role);
	#endif

	free(u);
}

Test(conversion)
{
	user_profile_t *u;
	struct passwd pwd = {
		.pw_uid = 0,
		.pw_name = "test-name",
		.pw_gecos = "test-title",
		.pw_dir = "/../",
		.pw_shell = "/bin/cat",
		#ifndef __linux__
			.pw_class = "test-role",
		#endif
	};

	u = user_profile_convert_pwd(&pwd);
	test(u != NULL);

	test->equality(0, u->u_identifier);
	test->strcmp("test-name", u->u_name);
	test->strcmp("test-title", u->u_title);
	test->strcmp("/../", u->u_home);
	test->strcmp("/bin/cat", u->u_shell);

	#ifndef __linux__
		test->strcmp("test-role", u->u_role);
	#else
		test->strcmp("", u->u_role);
	#endif

	free(u);
}

Test(cached_profile)
{
	const user_profile_t *u = current_user_profile();

	test->equality(getuid(), u->u_identifier);
	test->equality(u, current_user_profile());
	release_user_profile();
	test(!)->equality(NULL, current_user_profile());
}
