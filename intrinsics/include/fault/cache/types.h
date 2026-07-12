#if (UINTPTR_MAX == 0xFFFFFFFF)
	typedef uint32_t cache_uint_t;
#else
	typedef uint64_t cache_uint_t;
#endif

#ifndef CACHE_SOURCE_TEMPLATE
	typedef cache_uint_t cache_key_identity_t;
	typedef int32_t cache_umetric_t;
	#define CACHE_UMETRIC_LIMIT (INT32_MAX / 2)

	typedef void *cache_key_t;
	typedef void *cache_value_t;
#endif

struct CacheUsage
{
	#ifndef CACHE_USAGE_TRACKING
		cache_umetric_t u_hit, u_missed, u_rate;
	#endif
};

struct CacheRecord
{
	struct CacheUsage r_usage;

	cache_key_identity_t r_identity;

	#ifdef CACHE_SOURCE_TEMPLATE
		/* Defined by the instance. */
		cache_key_t r_key;
		cache_value_t r_value;
	#else
		struct {} r_key; // uint8_t r_key[cache_key_size()];
		struct {} r_value; // uint8_t r_value[cache_value_size()];
	#endif
};

const static size_t cache_record_header_size =
	(size_t) &((struct CacheRecord *) 0)->r_key;

struct CacheStorage
{
	size_t total_record_count;
	size_t allocation_size;
	size_t distribution_size;

	size_t *counts;
	size_t *slots;
	struct CacheRecord **records;
};

const static size_t cache_storage_size = sizeof(struct CacheStorage);

typedef struct CacheRecord * (*cache_record_f)(void *, struct CacheRecord *);
typedef struct CacheRecord * (*cache_slot_f)(struct CacheStorage *, int, cache_key_t *, cache_key_identity_t);
