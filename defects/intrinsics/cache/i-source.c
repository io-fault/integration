/**
	// Validate the source level template.
*/
#include <stdint.h>
#include <unistd.h>
#include <time.h>
#include <fault/libc.h>
#include <fault/metrics.h>
#include <fault/test.h>
#include <fault/hash.h>

#define CACHE_SYMBOL(S) override_##S
#include <fault/cache/rename.h>

typedef uint32_t cache_key_identity_t;
typedef int32_t cache_umetric_t;
#define CACHE_UMETRIC_LIMIT (INT32_MAX / 2)

struct Key { char pad[49]; uint32_t len; const char *str; };
struct Value { void *ptr; };
typedef struct Key cache_key_t;
typedef struct Value cache_value_t;

#include <fault/cache/template.h>

#define K(S) &((struct Key) {{0,0,1,0}, sizeof(S)-1, S})
#define V(I) &((struct Value) {I})

const size_t
cache_key_size(void)
{
	return(sizeof(struct Key));
}

const size_t
cache_value_size(void)
{
	return(sizeof(void *));
}

cache_key_identity_t
cache_key_identify(cache_key_t *key)
{
	uint32_t h = hash_32(0, key->str, key->len);
	return(h);
}

int
cache_key_compare(cache_key_t *k1, cache_key_t *k2)
{
	if (k1->len != k2->len)
		return(-1);
	return(memcmp(k1->str, k2->str, k1->len));
}

size_t
cache_distribution_index(cache_storage_t *c, cache_key_identity_t ki)
{
	return(ki % c->distribution_size);
}

void
cache_evict_record(cache_storage_t *c, cache_record_t r)
{
	;
}

void
cache_initialize_slot(cache_storage_t *c, cache_record_t r, size_t distribution, size_t slot)
{
	memset(r, 0, cache_record_size());
}

/**
	// Validate expectations.
*/
Test(first_constants)
{
	cache_record_t r;
	test->equality(cache_key_size(), sizeof(cache_key_t));
	test->equality(cache_value_size(), sizeof(cache_value_t));
	test->equality(cache_record_size(), sizeof(*r));
}

Test(first_usage)
{
	cache_record_t r;
	cache_storage_t cs, *c = &cs;

	test->equality(cache_initialize(c, 1, 1, 1), 0);
	test->equality(cache_initialized(c), true);
	test->equality(cache_record_count(c), 0);

	test->equality(cache_get(c, K("key")), NULL);
	cache_set(c, K("key"), V((void *) 12345678));
	test->equality(cache_get(c, K("key"))->ptr, 12345678);

	cache_release(c);
}

#define CACHE_SYMBOL(S) second_##S
#include <fault/cache/rename.h>

typedef uint64_t cache_key_identity_t;
typedef int16_t cache_umetric_t;
#define CACHE_UMETRIC_LIMIT (INT16_MAX / 2)

struct SecondKey { char pad[20]; uint32_t len; const char *str; };
struct SecondValue { void *ptr; int i };
typedef struct SecondKey cache_key_t;
typedef struct SecondValue cache_value_t;

#include <fault/cache/template.h>

#define K2(S) &((struct SecondKey) {{0,0,1,0}, sizeof(S)-1, S})
#define V2(I) &((struct SecondValue) {I})

const size_t
cache_key_size(void)
{
	return(sizeof(struct SecondKey));
}

const size_t
cache_value_size(void)
{
	return(sizeof(struct SecondValue));
}

cache_key_identity_t
cache_key_identify(cache_key_t *key)
{
	struct Key *ks = key;
	return(hash_64(0, ks->str, ks->len));
}

int
cache_key_compare(cache_key_t *k1, cache_key_t *k2)
{
	if (k1->len != k2->len)
		return(-1);
	return(memcmp(k1->str, k2->str, k1->len));
}

size_t
cache_distribution_index(cache_storage_t *c, cache_key_identity_t ki)
{
	return(ki % c->distribution_size);
}

void
cache_evict_record(cache_storage_t *c, cache_record_t r)
{
	;
}

void
cache_initialize_slot(cache_storage_t *c, cache_record_t r, size_t distribution, size_t index)
{
	memset(r, 0, cache_record_size());
}
