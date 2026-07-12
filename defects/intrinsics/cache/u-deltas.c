/**
	// Validate cache manipulation interfaces.
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

Test(delete)
{
	cache_value_t *v;
	cache_record_t r, k1, k2;
	cache_storage_t cs, *c = &cs;

	cache_initialize(c, 1, 1, 1);
	v = cache_set(c, K("key"), V("value"));
	test->equality(cache_record_count(c), 1);
	test->equality(cache_delete(c, K("key")), v);
	test->equality(cache_record_count(c), 0);
	test->equality(c->counts[0], 0);

	test->equality(*cache_set(c, K("key-1"), V(1)), 1);
	test->equality(*cache_set(c, K("key-2"), V(2)), 2);
	test->equality(cache_record_count(c), 2);

	test->equality(*cache_delete(c, K("key-1")), 1);
	test->equality(cache_record_count(c), 1);

	test->equality(*cache_delete(c, K("key-2")), 2);
	test->equality(cache_record_count(c), 0);
	test->equality(c->counts[0], 0);

	cache_release(c);
}

/**
	// Validate cache_insert's behavior.
*/
Test(insert)
{
	cache_record_t r, r2;
	cache_storage_t cs, *c = &cs;
	cache_value_t v = (cache_value_t) 987654;
	cache_value_t v2 = (cache_value_t) 0;

	cache_initialize(c, 1, 1, 1);

	r = cache_insert_record(c, K("key"), &v);
	test->equality(cache_select_record(c, K("key")), r);
	test->equality(*(int *) cache_record_value(r), 987654);

	// The new key is inserted after the first.
	r2 = cache_insert_record(c, K("key"), &v2);
	test->equality(*(int *) cache_get(c, K("key")), v);
	test->equality(*(int *) cache_record_value(r2), 0);

	cache_release(c);
}

/**
	// Validate cache_update's behavior.
*/
Test(update)
{
	cache_record_t r;
	cache_storage_t c;
	cache_value_t *v;
	cache_initialize(&c, 1, 2, 1);

	v = cache_set(&c, K("key-1"), V(999));
	test->truth(sizeof(V(0)) > 0);
	test->memcmp(v, V(999), sizeof(V(0)));

	test->equality(cache_update(&c, K("key-1"), V(888)), v);
	test->memcmp(v, V(888), sizeof(V(0)));

	cache_release(&c);
}

/**
	// Validate cache_default's behavior.
*/
Test(default)
{
	cache_record_t r;
	cache_storage_t c;
	cache_value_t *v;
	cache_initialize(&c, 1, 2, 1);

	v = cache_set(&c, K("key-1"), V(999));
	test->truth(sizeof(V(0)) > 0);
	test->memcmp(v, V(999), sizeof(V(0)));

	// Not inserted.
	test->equality(cache_default(&c, K("key-1"), V(888)), v);
	test->memcmp(v, V(999), sizeof(V(0)));

	// Inserted.
	test->memcmp(cache_default(&c, K("key-2"), V(888)), V(888), sizeof(V(0)));

	cache_release(&c);
}
