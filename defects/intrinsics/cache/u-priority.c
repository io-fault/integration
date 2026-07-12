/**
	// Validate record prioritization.
*/
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/metrics.h>
#include <fault/test.h>

#include <fault/hash.h>
#include <fault/cache/factor.h>

struct Key { size_t len; const char *str; };
struct Value { void *ptr; };

#define K(S) &((struct Key) {sizeof(S)-1, S})
#define V(I) &((struct Value) {(void *)I})

#define INSERT(C, k, v) (cache_set(&C, K(k), V(v)))
#define SELECT(C, k) (*cache_get(&C, K(k)))
#define VOID(C, k) (cache_get(&C, K(k))==NULL)

void
cache_evict_record(cache_storage_t *, cache_record_t r)
{
	cache_record_set_value(r, V(NULL));
}

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

Test(defaults)
{
	cache_record_t r;
	cache_storage_t c;
	cache_initialize(&c, 4, 4, 1);

	INSERT(c, "", 100);

	r = cache_select_record(&c, K(""));
	test->equality(r->r_usage.u_hit, 1);
	test->equality(r->r_usage.u_missed, 1);
	test->equality(r->r_usage.u_rate, 1);

	cache_release(&c);
}

/**
	// Validate usage increments on requests.
*/
Test(requests)
{
	cache_record_t r1, r2;
	cache_storage_t c;

	// Only one bucket here so that misses increment without having
	// spend time finding distribution aligned keys.
	cache_initialize(&c, 1, 4, 1);

	INSERT(c, "", 100);

	r1 = cache_request_record(&c, K(""));
	test->equality(r1->r_usage.u_hit, 2);
	test->equality(r1->r_usage.u_missed, 1);

	test->equality(cache_request(&c, K("")), cache_record_value(r1));
	test->equality(r1->r_usage.u_hit, 3);
	test->equality(r1->r_usage.u_missed, 1);

	test->equality(cache_request(&c, K("miss")), NULL);
	test->equality(r1->r_usage.u_hit, 3);
	test->equality(r1->r_usage.u_missed, 2);

	test->equality(cache_request_record(&c, K("miss")), NULL);
	test->equality(r1->r_usage.u_hit, 3);
	test->equality(r1->r_usage.u_missed, 3);

	INSERT(c, "priority", 505);
	r2 = cache_request_record(&c, K("priority"));
	test->truth(r1 < r2);
	test->truth(r2 != NULL);
	test->equality(r1->r_usage.u_missed, 4);

	/*
		// These checks are intended to validate the motion rather
		// than a specific prioritization behavior.
	*/

	for (int i = 0; i < CACHE_USAGE_THRESHOLD * 4; ++i)
		cache_request(&c, K("priority"));
	test(!)->equality(cache_select_record(&c, K("")), r1);
	test->equality(cache_select_record(&c, K("priority")), r1);
	test->equality(cache_select_record(&c, K("")), r2);

	for (int i = 0; i < CACHE_USAGE_THRESHOLD; ++i)
		cache_request(&c, K(""));
	test->equality(cache_select_record(&c, K("priority")), r1);
	test->equality(cache_select_record(&c, K("")), r2);

	for (int i = 0; i < CACHE_USAGE_THRESHOLD * 2; ++i)
		cache_request(&c, K(""));
	test->equality(cache_select_record(&c, K("")), r1);
	test->equality(cache_select_record(&c, K("priority")), r2);

	cache_release(&c);
}

static cache_record_t
rf(void *ctx, cache_record_t new)
{
	static void *i = 0;
	++i;

	cache_record_set_value(new, (void *) &i);
	return(new);
}

/**
	// Validate usage increments on requires.
*/
Test(requires)
{
	cache_record_t r1, r2, r3;
	cache_storage_t c;

	// Only one bucket here so that misses increment without having
	// spend time finding distribution aligned keys.
	cache_initialize(&c, 1, 4, 1);
	#define c_require_record(k) \
		cache_require_record(&c, K(k), cache_acquire_slot, rf, (void *) test)
	#define c_require(k) \
		cache_require(&c, K(k), cache_acquire_slot, rf, (void *) test)

	INSERT(c, "", 100);

	r1 = c_require_record("");
	test->equality(r1->r_usage.u_hit, 2);
	test->equality(r1->r_usage.u_missed, 1);

	test->equality(c_require(""), cache_record_value(r1));
	test->equality(r1->r_usage.u_hit, 3);
	test->equality(r1->r_usage.u_missed, 1);

	test->equality(*c_require("miss"), (void *) 1);
	test->equality(r1->r_usage.u_hit, 3);
	test->equality(r1->r_usage.u_missed, 2);

	test->equality(*c_require("miss"), (void *) 1);
	test->equality(r1->r_usage.u_hit, 3);
	test->equality(r1->r_usage.u_missed, 3);

	r2 = cache_select_record(&c, K("miss"));
	INSERT(c, "priority", 505);
	r3 = c_require_record("priority");

	test->truth(r1 < r2);
	test->truth(r2 < r3);
	test->truth(r2 != NULL);
	test->truth(r3 != NULL);
	test->equality(r1->r_usage.u_missed, 4);
	test->equality(cache_record_count(&c), 3);

	/*
		// These checks are intended to validate the motion rather
		// than a specific prioritization behavior.
	*/

	for (int i = 0; i < CACHE_USAGE_THRESHOLD * 2; ++i)
		c_require("priority");
	test->equality(cache_select_record(&c, K("")), r1);
	test->equality(cache_select_record(&c, K("priority")), r2);
	test->equality(cache_select_record(&c, K("miss")), r3);

	for (int i = 0; i < CACHE_USAGE_THRESHOLD * 6; ++i)
		c_require("miss");
	test->equality(cache_select_record(&c, K("miss")), r1);
	test->equality(cache_select_record(&c, K("")), r2);
	test->equality(cache_select_record(&c, K("priority")), r3);
	test->equality(cache_record_count(&c), 3);

	for (int i = 0; i < CACHE_USAGE_THRESHOLD * 4; ++i)
		c_require("");
	test->equality(cache_select_record(&c, K("")), r1);
	test->equality(cache_select_record(&c, K("miss")), r2);
	test->equality(cache_select_record(&c, K("priority")), r3);
	test->equality(cache_record_count(&c), 3);

	cache_release(&c);
	#undef c_require
	#undef c_require_record
}

/**
	// Validate requires behavior when fixed slot acquisition is selected.
*/
Test(require_recycle)
{
	cache_record_t r1, r2, r3, r4;
	cache_storage_t c;

	// Initialize four slots with an allocation size of two.
	cache_initialize(&c, 1, 2, 2);
	#define c_require_record(k) \
		cache_require_record(&c, K(k), cache_acquire_slot_fixed, rf, (void *) test)

	r1 = c_require_record("first");
	r2 = c_require_record("second");
	r3 = c_require_record("third");
	r4 = c_require_record("fourth");
	test->equality(cache_record_count(&c), 4);

	// With allocation size of two, the last two slots will be reused.
	test->equality(c_require_record("fifth"), r3);

	// r4 was evicted. Validate the NULL set by &cache_evict_record.
	test->equality(*cache_record_value(r4), NULL);

	// Use r4, check rf's update of the value.
	test->equality(c_require_record("sixth"), r4);
	test->truth(*cache_record_value(r4) > 0);

	// Check the cycle once again.
	test->equality(c_require_record("seventh"), r3);

	cache_release(&c);
	#undef c_require_record
}
