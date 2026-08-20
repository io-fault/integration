/**
	// Validate executable inquiries.
*/
#include <float.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>
#include <inttypes.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/clock.h>
#include <fault/metrics.h>
#include <fault/test.h>
#include <fault/query.h>

Test(path_empty)
{
	path_vector_t *pv;

	setenv("TESTPATH", "", 1);
	pv = executable_paths("TESTPATH");

	test->equality(1, pv->path_count);
	test->equality(0, pv->path_maximum_length);

	test->strcmp("", pv->path_strings[0]);
	test->equality(NULL, pv->path_strings[1]);

	free(pv);
}

Test(path_list)
{
	path_vector_t *pv;

	setenv("TESTPATH", "a:b:/c", 1);
	pv = executable_paths("TESTPATH");

	test->equality(3, pv->path_count);
	test->equality(2, pv->path_maximum_length);

	test->strcmp("a", pv->path_strings[0]);
	test->strcmp("b", pv->path_strings[1]);
	test->strcmp("/c", pv->path_strings[2]);

	free(pv);
}

Test(path_default)
{
	int i = 0;
	path_vector_t *paths1, *paths2;

	paths1 = executable_paths("PATH");
	paths2 = executable_paths(NULL);

	while(paths1->path_strings[i] != NULL)
	{
		test->strcmp(paths1->path_strings[i], paths2->path_strings[i]);
		++i;
	}

	test->equality(paths1->path_strings[i], NULL);
	test->equality(paths2->path_strings[i], NULL);

	test->equality(paths1->path_count, i);
	test->equality(paths2->path_count, i);

	free(paths1);
	free(paths2);
}

Test(tee_path)
{
	const char *path;

	path = executable_first("tee");
	test->strcmp("/usr/bin/tee", path);
	free(path);
}

Test(executable_not_found)
{
	const char *path;

	setenv("PATH", "/../", 1);
	path = executable_first("not-found");
	test->equality(NULL, path);
}
