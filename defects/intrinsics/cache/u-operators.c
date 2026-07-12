/**
	// Validate cache operators.
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

#define INSERT(C, k, v) (cache_set(&C, K(k), V(v)))
#define SELECT(C, k) (*cache_get(&C, K(k)))
#define VOID(C, k) (cache_get(&C, K(k))==NULL)

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
	uint32_t h = hash_32(0, ks->str, ks->len);
	return(h);
}

Test(extend_records)
{
	cache_storage_t dst, src;
	cache_initialize(&dst, 4, 4, 1);
	cache_initialize(&src, 4, 4, 1);

	INSERT(dst, "key-0", 'z');
	INSERT(dst, "key-1", 'd');
	INSERT(src, "key-1", 'a');
	INSERT(src, "key-2", 'b');
	INSERT(src, "key-3", 'c');

	test->equality(cache_extend_records(&dst, &src), 2);
	test->equality(cache_record_count(&dst), 4);

	test->equality(SELECT(dst, "key-0"), 'z');
	test->equality(SELECT(dst, "key-1"), 'd');
	test->equality(SELECT(dst, "key-2"), 'b');
	test->equality(SELECT(dst, "key-3"), 'c');

	cache_release(&dst);
	cache_release(&src);
}

Test(replace_records)
{
	cache_storage_t dst, src;
	cache_initialize(&src, 4, 4, 1);
	cache_initialize(&dst, 4, 4, 1);

	INSERT(dst, "replace-1", 101);
	INSERT(src, "replace-1", 202);
	INSERT(src, "replace-2", 1);
	test->equality(cache_replace_records(&dst, &src), 2);

	test->equality(SELECT(dst, "replace-1"),  202);
	test->equality(SELECT(dst, "replace-2"),  1);
}

Test(update_records)
{
	cache_storage_t dst, src;
	cache_initialize(&src, 4, 4, 1);
	cache_initialize(&dst, 4, 4, 1);

	INSERT(src, "updated", 505);
	INSERT(src, "ignored", 404);
	INSERT(dst, "updated", 101);

	test->truth(VOID(dst, "ignored"));
	test->equality(SELECT(dst, "updated"), 101);
	test->equality(cache_update_records(&dst, &src), 1);
	test->equality(SELECT(dst, "updated"), 505);
	test->equality(cache_record_count(&dst), 1);
}

Test(discard_records)
{
	cache_storage_t dst, src;
	cache_initialize(&src, 4, 4, 1);
	cache_initialize(&dst, 4, 4, 1);

	INSERT(dst, "kept", 100);
	INSERT(dst, "removed", 200);
	INSERT(src, "removed", 1000);

	test->truth(!VOID(dst, "kept"));
	test->truth(!VOID(dst, "removed"));
	test->equality(cache_record_count(&dst), 2);
	test->equality(cache_discard_records(&dst, &src), 1);
	test->truth(VOID(dst, "removed"));
	test->equality(cache_record_count(&dst), 1);
}

Test(truncate_records)
{
	cache_storage_t c;
	cache_initialize(&c, 8, 4, 1);

	INSERT(c, "removed-1", 100);
	INSERT(c, "removed-2", 200);
	INSERT(c, "removed-3", 300);
	INSERT(c, "removed-4", 400);
	test->equality(cache_record_count(&c), 4);

	test->equality(cache_truncate_records(&c), 4);
	test->truth(VOID(c, "removed-1"));
	test->truth(VOID(c, "removed-2"));
	test->truth(VOID(c, "removed-3"));
	test->truth(VOID(c, "removed-4"));
	test->equality(cache_record_count(&c), 0);
}

cache_record_t
fr(void *ctx, cache_record_t r)
{
	struct { size_t total; size_t count; } *state = ctx;
	state->total += (size_t) *cache_record_value(r);
	state->count += 1;
	return(r);
}

Test(scan_records)
{
	struct { size_t total; size_t count; } state = {0,0};
	cache_storage_t c;
	cache_initialize(&c, 4, 4, 1);

	INSERT(c, "scanned-1", 100);
	INSERT(c, "scanned-2", 200);
	INSERT(c, "scanned-3", 300);
	INSERT(c, "scanned-4", 400);
	test->equality(cache_record_count(&c), 4);

	test->equality(cache_scan_records(&c, fr, (void *) &state), 4);
	test->equality(state.total, 100 + 200 + 300 + 400);
	test->equality(state.count, 4);
}

Test(redistribute_records)
{
	cache_storage_t c;
	cache_initialize(&c, 1, 2, 1);

	INSERT(c, "moved-1", 100);
	INSERT(c, "moved-2", 200);
	INSERT(c, "moved-3", 300);
	INSERT(c, "moved-4", 400);
	test->equality(cache_record_count(&c), 4);

	test->equality(cache_redistribute_records(&c, 8), 0);
	test->equality(SELECT(c, "moved-1"), 100);
	test->equality(SELECT(c, "moved-2"), 200);
	test->equality(SELECT(c, "moved-3"), 300);
	test->equality(SELECT(c, "moved-4"), 400);
}
