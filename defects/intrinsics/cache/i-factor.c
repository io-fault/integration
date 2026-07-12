/**
	// Validate the cache's functionality when linked against the factor.
*/
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/metrics.h>
#include <fault/test.h>

#include <fault/hash.h>
#include <fault/cache/factor.h>

struct Key { uint32_t len; const char *str; };
struct Value { void *ptr; };
#define K(S) &((struct Key) {sizeof(S)-1, S})
#define V(I) &((struct Value) {(void *)I})

const size_t
cache_key_size(void)
{
	return(sizeof(struct Key));
}

int
cache_key_compare(cache_key_t *vk1, cache_key_t *vk2)
{
	struct Key *k1 = vk1, *k2 = vk2;

	if (k1->len != k2->len)
		return(-1);

	return(memcmp(k1->str, k2->str, k1->len));
}

cache_key_identity_t
cache_key_identify(cache_key_t *key)
{
	struct Key *ks = key;
	return(cache_identify_data(ks->str, ks->len));
}

/**
	// Validate overrides.
*/
Test(constants)
{
	test->equality(cache_key_size(), sizeof(struct Key));
	test->equality(cache_value_size(), sizeof(void *));
}

/**
	// Check initialziation and release.
*/
Test(storage_lifecycle)
{
	cache_record_t r;
	cache_storage_t cs, *c = &cs;

	cache_initialize(c, 128, 8, 1);
	test->equality(cache_initialized(c), true);
	test->equality(c->allocation_size, 8);
	test->equality(c->distribution_size, 128);
	test->equality(cache_record_capacity(c), 8 * 128);
	test->equality(cache_record_count(c), 0);

	cache_set(c, K("string"), V("test"));
	test->equality(cache_record_count(c), 1);
	test->equality(c->counts[cache_key_identify(K("string")) % c->distribution_size], 1);
	test->strcmp(*cache_get(c, K("string")), "test");
	test->equality(cache_record_count(c), 1);

	cache_release(c);
	test->equality(cache_initialized(c), false);
	test->equality(c->counts, NULL);
	test->equality(c->slots, NULL);
	test->equality(c->records, NULL);
}

/**
	// Check initialziation failure of zero sized caches.
*/
Test(empty)
{
	cache_record_t r;
	cache_storage_t cs = {0,}, *c = &cs;

	test->equality(cache_initialize(c, 0, 0, 0), -2);
	test->equality(cache_initialized(c), false);
}

/**
	// Check edge cases of 1x1 cache.
*/
Test(one)
{
	cache_record_t r;
	cache_storage_t cs, *c = &cs;

	test->equality(cache_initialize(c, 1, 1, 1), 0);
	test->equality(cache_initialized(c), true);
	test->equality(cache_record_count(c), 0);

	r = cache_set(c, K("key"), V("value"));
	test->equality(cache_record_count(c), 1);

	cache_release(c);
}

Test(record_capacity)
{
	cache_record_t r;
	cache_storage_t cs, *c = &cs;

	cache_initialize(c, 5, 10, 1);
	test->equality(cache_record_capacity(c), 10 * 5);
	cache_release(c);

	cache_initialize(c, 4, 2, 1);
	test->equality(cache_record_capacity(c), 2 * 4);
	cache_release(c);
}

Test(record_count)
{
	cache_record_t r;
	cache_storage_t cs, *c = &cs;
	cache_initialize(c, 1, 2, 1);

	test->equality(cache_record_count(c), 0);
	cache_set(c, K("string-1"), V(1));
	test->equality(cache_record_count(c), 1);
	cache_set(c, K("string-2"), V(2));
	test->equality(cache_record_count(c), 2);
	cache_set(c, K("string-3"), V(3));
	test->equality(cache_record_count(c), 3);

	cache_release(c);
}
