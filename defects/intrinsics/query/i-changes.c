/**
	// Validate that changes in usage can be observed.
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

static void *
__attribute__((optimize("O0")))
spin_cpu(int iteration_factor)
{
	int *v;
	v = malloc(sizeof(int) * 11);
	for (int i = 0; i < 10; ++i)
		v[i] = i + 10;
	v[10] = 100;

	for (int i = 0; i < 1000000 * iteration_factor; ++i)
	{
		int index = 0;
		for (int index = 0; index < 10; ++index)
		{
			v[index] += 20;
			v[index] *= v[index+1];
			v[index] /= 3;
		}
	}
	return(v);
}

__attribute__((optimize("O0")))
Test(cpu_usage)
{
	process_metrics_t pm1 = {0,};
	process_metrics_t pm2 = {0,};
	pid_t p = getpid();

	process_usage_scan(&pm1, p, 1);

	// Likely fragile.
	for (int i = 0; i < 3; ++i)
		free(spin_cpu(1));

	process_usage_scan(&pm2, p, 1);
	test->truth(pm2.total_user_time > pm1.total_user_time);
}

#include <sys/mman.h>

Test(memory_usage)
{
	process_metrics_t pm1 = {0,};
	process_metrics_t pm2 = {0,};
	process_metrics_t pm3 = {0,};
	pid_t p = getpid();
	void *m;
	size_t sz;

	process_usage_scan(&pm1, p, 1);

	// malloc doesn't seem to work well here.
	sz = 1000 * 1000 * 10;
	m = mmap(NULL, sz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	memset(m, 0xFF, sz);
	memset(m, 0x7F, sz);
	free(spin_cpu(1)); // delay (freebsd@15 seems to want some time for maxrss to update)

	process_usage_scan(&pm2, p, 1);
	test->truth(pm2.average_memory > pm1.average_memory);
	test->truth(pm2.average_maximum_memory > pm1.average_maximum_memory);
	test->truth(pm2.maximum_memory > pm1.maximum_memory);

	munmap(m, sz);
	free(spin_cpu(1)); // delay

	process_usage_scan(&pm3, p, 1);
	test->truth(pm3.average_memory < pm2.average_memory);

	#if defined(__linux__)
		// For sole processes, this is the VmHWM field.
		// Apparently, the water mark can go down.
		test->truth(abs(pm3.average_maximum_memory - pm2.average_maximum_memory) < 1000 * 100);
		test->truth(abs(pm3.maximum_memory - pm2.maximum_memory) < 1000 * 100);
	#else
		test->truth(pm3.average_maximum_memory >= pm2.average_maximum_memory);
		test->truth(pm3.maximum_memory >= pm2.maximum_memory);
	#endif
}
