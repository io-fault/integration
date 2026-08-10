/**
	// Check process_metrics_t operators.
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

Test(combine_averages)
{
	process_metrics_t pm[] = {
		{.process_count = 100, .average_maximum_memory = 400,
			.maximum_elapsed_time = 100.0, .maximum_memory = 2.0},
		{.process_count = 100, .average_memory = 200,
			.maximum_elapsed_time = 300.0, .maximum_memory = 1.0},

		// With a zero process_count, the value is discarded.
		{.average_maximum_memory = 2000, .average_memory = 2000,
			.maximum_elapsed_time = 200.0, .maximum_memory = 3.0},
	};
	process_metrics_t r = {0,};

	process_metrics_combine(&r, (process_metrics_t *[]){&pm[0], &pm[1], &pm[2], NULL});
	test->equality(200, r.process_count);
	test->equality(100, r.average_memory);
	test->equality(200, r.average_maximum_memory);
}

Test(combine_maximums)
{
	process_metrics_t pm[] = {
		{.maximum_elapsed_time = 100.0, .maximum_memory = 2.0},
		{.maximum_elapsed_time = 300.0, .maximum_memory = 1.0},
		{.maximum_elapsed_time = 200.0, .maximum_memory = 3.0},
	};
	process_metrics_t r = {0,};

	process_metrics_combine(&r, (process_metrics_t *[]){&pm[0], &pm[1], &pm[2], NULL});
	test->equality(300.0, r.maximum_elapsed_time);
	test->equality(3.0, r.maximum_memory);
}

#define PMTC(P, T, Z, S, L) \
	.process_count=P, .thread_count=T, .zombie_count=Z, \
	.suspended_count=S, .locked_count=L
#define PMTT(C, U, S) \
	.total_cumulative_time=C, .total_user_time=U, .total_system_time=S

Test(combine_sums)
{
	int r;
	process_metrics_t pm[] = {
		{PMTC(2, 2, 2, 2, 2), PMTT(20.0, 2*20.0, 3*20.0)},
		{PMTC(3, 3, 3, 3, 3), PMTT(30.0, 2*30.0, 3*30.0)},
		{PMTC(4, 4, 4, 4, 4), PMTT(40.0, 2*40.0, 3*40.0)},
	};
	process_metrics_t r = {0,};

	r = process_metrics_combine(&r, (process_metrics_t *[]){&pm[0], &pm[1], &pm[2], NULL});
	test->equality(3, r);
	test->equality(9, r.process_count);
	test->equality(9, r.thread_count);
	test->equality(9, r.zombie_count);
	test->equality(9, r.suspended_count);
	test->equality(9, r.locked_count);
	test->equality(1*90.0, r.total_cumulative_time);
	test->equality(2*90.0, r.total_user_time);
	test->equality(3*90.0, r.total_system_time);
}
