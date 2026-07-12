/**
	// Validate the cache's default parameters and miscellaneous functions.
*/
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/metrics.h>
#include <fault/test.h>

#include <fault/hash.h>
#include <fault/cache/factor.h>

/**
	// Check the default parameters often replaced by other tests.
*/
Test(parameters)
{
	cache_record_t r;
	cache_storage_t cs, *c = &cs;
	void *k = (void *)300, *v = (void *)500;

	test->equality(cache_initialize(c, 1, 1, 1), 0);

	test->equality(cache_key_size(), sizeof(void *));
	test->equality(cache_value_size(), sizeof(void *));

	r = cache_set(c, &k, &v);
	test->equality(cache_record_count(c), 1);

	// Trigger the default key_compare.
	test->equality(*cache_get(c, &k), v);

	cache_release(c);
}

/**
	// Check get/set key/value.
*/
Test(record_gets_and_sets)
{
	cache_record_t r;
	cache_storage_t c;
	void *k = (void *) 100, *v = (void *) 200;
	void *dk = (void *) 1, *dv = (void *) 2;

	test->equality(cache_initialize(&c, 1, 1, 1), 0);
	cache_set(&c, &k, &v);

	r = cache_select_record(&c, &k);
	test->truth(r != NULL);
	test->equality(*cache_record_key(r), k);
	test->equality(*cache_record_value(r), v);

	// Usually unused as the key is configured when allocated.
	test->equality(cache_record_set_key(r, &dk), cache_record_key(r));

	// key identity should match, but the memcmp shouldn't.
	test->equality(cache_get(&c, &k), NULL);
	test->equality(*cache_record_set_value(r, &dv), dv);

	// Reset
	test->equality(cache_record_set_key(r, &k), cache_record_key(r));
	test->equality(cache_record_set_value(r, &v), cache_record_value(r));
	test->equality(cache_get(&c, &k), cache_record_value(r));

	cache_release(&c);
}
