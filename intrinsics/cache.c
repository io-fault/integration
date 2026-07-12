/**
	// Hash table based container template for permanent directories and temporary caches.

	// Templating can be applied at either the source or linker level given weak
	// symbol support. When source level templating is not being used, the default
	// &[Parameters] (functions) will be provided with the expectation of overrides
	// being defined by other object files. LTO compilation is advisable to avoid
	// the high frequency overhead of functions returning constants.

	// [ Thread Safety & Record Memory Usage ]
	// The current implementation makes no attempt protect concurrent access, so
	// non-read operations performed against the same &cache_storage_t instance across
	// threads will likely cause corruption.

	// Furthermore, prioritization and deletion may cause records to be moved. Pointers to
	// values, keys, and entire records should be used or copied prior to performing
	// subsequent deletion or prioritized access on the instance.

	// [ Prioritization ]
	// Record usage is tracked, by default, in order to move frequently accessed records
	// to the beginning of their distributions. However, only some access methods register
	// hits and misses:

	// - &cache_require_record
	// - &cache_require
	// - &cache_request_record
	// - &cache_request

	// [ Parameters ]
	// The set of functions that may be overridden to accommodate the instance's needs.
	// For source level templates, all of these functions need to be defined or declared.

	// /&cache_key_size/
		// The fixed key size.
	// /&cache_value_size/
		// The fixed value size.
	// /&cache_identify_data/
		// Direct hash function taking the memory pointer and size.
	// /&cache_key_identify/
		// The caller of the hash function selecting the parts of the key to be identified.
	// /&cache_key_compare/
		// Key comparison returning zero when equal.
	// /&cache_distribution_index/
		// Distribution selector. Defaults to `key_identity_t % c->distribution_size`.
	// /&cache_evict_record/
		// Executed when a record is deleted or reclaimed as a slot.
		// Used to release key or value resources.
	// /&cache_initialize_slot/
		// Initializes a record's slot. Called during slot allocation and primarily
		// intended for fixed caches whose records have constant values.

	// [ Source Level Template ]
	// The source level template is instantiated by including `cache/template.h`, but
	// usage requires a fair amount of boilerplate:
	// #!syntax/c
		// // Optional requirement index.
		#include <fault/cache/context.h>

		// // Rename identifiers to use `local_prefix_*`
		// // The cache_* names may still be used as they are defined in `cache/rename.h`.
		#define CACHE_SYMBOL(S) local_prefix_##S
		#include <fault/cache/rename.h>

		// // Define the metric size.
		typedef int32_t cache_umetric_t;

		// // Hits and misses are tracked; constrain to half the maximum
		// // so that they may be safely summed when calculating the rate.
		#define CACHE_UMETRIC_LIMIT (INT32_MAX / 2)

		// // Key hash identity size and structures for the key and value.
		typedef uint64_t cache_key_identity_t;
		typedef struct {...} cache_key_t;
		typedef struct {...} cache_value_t;

		#include <fault/cache/template.h>

		// // Default parameter functions are disabled by `template.h`,
		// // so the entire set should be defined here.

	// [ Controls ]
	// Tunables for source level templating.

	// /`CACHE_SYMBOL`/
		// Macro used to control symbol names along with the `cache/rename.h`.
	// /`CACHE_USAGE_THRESHOLD`/
		// The number of hit and miss events needed to consider prioritization.
	// /`CACHE_USAGE_SWAP_MINIMUM`/
		// The rate difference required to cause a record to be swapped.
	// /`CACHE_USAGE_RATE_DECAY`/
		// The fraction of the rate that should be maintained across usage
		// thresholds. Expressed as a whole number used as the divisor.
	// /`CACHE_MEMORY_ALLOCATE`/
		// Memory allocate macro taking a cache instance.
	// /`CACHE_MEMORY_REALLOCATE`/
		// Memory reallocate macro taking a cache instance.
	// /`CACHE_MEMORY_RELEASE`/
		// Memory release (free) macro taking a cache instance.

	// [ Definitions ]
	// /storage/
		// A collection of records functionally derived or arbitrarily constructed.
		// Currently, this is only implemented as a hash table.
	// /record/
		// A key and value associated with usage metrics.
	// /slot/
		// A range of allocated memory capable of holding a record.
	// /distribution/
		// A slice of record slots that make up part of a cache instance.
		// Often, with respect to an index identifying the slice.

	// [ Shorthands ]
	// /c/
		// A pointer to a cache storage: &cache_storage_t.
	// /r/
		// A pointer to a cache record: &cache_record_t.
	// /k/
		// A pointer to a record's key: &cache_key_t.
	// /v/
		// A pointer to a record's value: &cache_value_t.
	// /ki/
		// A key's identity: &cache_key_identity_t.
	// /di/
		// The index of the distribution. (bucket index)
	// /f/
		// A pointer to the cache's mapping function: &cache_record_f.
*/
#ifndef CACHE_SOURCE_TEMPLATE
	#include <fault/cache/context.h>
	#include <fault/libc.h>
	#define FAULT_METRICS_LINKED
	#include <fault/metrics.h>

	/**
		// Default pointer type identifying record key memory.

		// Respected storage size being defined by &cache_key_size.
	*/
	typedef void *cache_key_t;

	/**
		// Default pointer type identifying record value memory.

		// Respected storage size being defined by &cache_value_size.
	*/
	typedef void *cache_value_t;

	#include <fault/cache/control.h>
	#include <fault/cache/types.h>

	/**
		// The storage for a key's identity.
	*/
	typedef cache_uint_t cache_key_identity_t;

	/**
		// Hash table implementation with record prioritization.

		// [ Parameters ]
		// /allocation_size/
			// The allocation delta to use when resizing a record set.
		// /distribution_size/
			// The number of record sets currently allocated.

		// /counts/
			// The number of allocated records in the distribution.
		// /slots/
			// The total number of slots in the distribution.
			// Where `counts[cdi]` - `slots[cdi]` are immediately available.
		// /records/
			// The distributions of records contained by the cache.
	*/
	typedef struct CacheStorage cache_storage_t;

	/**
		// Record entry in &cache_storage_t providing the key, value, and usage.
	*/
	typedef struct CacheRecord *cache_record_t;

	/**
		// Function pointer type used by &cache_require to handle
		// lookup exception cases.
	*/
	typedef struct CacheRecord * (*cache_record_f)(void *, struct CacheRecord *);

	/**
		// Slot acquisition method for controlling &cache_require behavior for fixed allocation
		// cache instances.
	*/
	typedef struct CacheRecord * (*cache_slot_f)(struct CacheStorage *, int, cache_key_t *, cache_key_identity_t);

	#include <fault/cache/parameters.h>
	#include <fault/cache/interfaces.h>
	#include <fault/cache/prototypes.h>

	// Allow dependents to override these for link time templating.
	#define CACHE_DEFAULT_PARAMETER \
		CACHE_PARAMETER_QUALIFIERS \
		extern inline __attribute__((weak))

	/**
		// The size of a record's key.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER const size_t
	cache_key_size(void)
	{
		return(sizeof(void *));
	}

	/**
		// The size of a record's value.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER const size_t
	cache_value_size(void)
	{
		return(sizeof(void *));
	}

	/**
		// Whether or not two keys should be considered equivalent.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER int
	cache_key_compare(cache_key_t *k1, cache_key_t *k2)
	{
		return(memcmp(k1, k2, cache_key_size()));
	}

	/**
		// Identify the data referenced by &pointer.
		// Defaults to &cache_default_hash.

		// Used by &cache_identify_key.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER cache_key_identity_t
	cache_identify_data(void *pointer, size_t length)
	{
		return(cache_default_hash(pointer, length));
	}

	/**
		// Identify a key. The hash function used to determine
		// a record's distribution and possible equivalence.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER cache_key_identity_t
	cache_key_identify(cache_key_t *key)
	{
		return(cache_identify_data(key, cache_key_size()));
	}

	/**
		// Select the distribution to use for the given identity.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER size_t
	cache_distribution_index(cache_storage_t *c, cache_key_identity_t ki)
	{
		return(ki % c->distribution_size);
	}

	/**
		// Function performed when a record is to be removed from a cache.

		// By default, nothing.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER void
	cache_evict_record(cache_storage_t *c, cache_record_t r)
	{
		;
	}

	/**
		// Function performed when a slot is allocated during initialization
		// and during use when an insert causes a distribution to be resized.

		// By default, zero the record's allocation.

		// &[Parameters]
	*/
	CACHE_DEFAULT_PARAMETER void
	cache_initialize_slot(cache_storage_t *c, cache_record_t r, size_t distribution, size_t index)
	{
		memset(r, 0, cache_record_size());
	}
#endif

#define cache_record_scan_loop(NAME, KEY, KI, RECORDS, COUNT) \
	for (cache_record_t NAME = RECORDS, NAME##_END=cache_record_index(RECORDS, COUNT); \
		NAME != NAME##_END; \
		NAME = cache_record_next(NAME)) \
	if (cache_record_matches(NAME, KEY, KI))

#define cache_record_scan_context(NAME, CACHE, KEY) \
	cache_key_identity_t NAME##_ki = cache_key_identify(KEY); \
	int NAME##_di = cache_distribution_index(CACHE, NAME##_ki); \
	size_t NAME##_rcount = CACHE->counts[NAME##_di]; \
	cache_record_t NAME##_first = CACHE->records[NAME##_di];

#define cache_record_scan_distributions(NAME, CACHE) \
	for (size_t NAME##_ds = CACHE->distribution_size, \
		NAME##_di = 0; NAME##_di < NAME##_ds; ++ NAME##_di)

#define cache_record_scan_distribution_records(NAME, RECORDS, COUNTS) \
	for (cache_record_t \
		NAME##_first = RECORDS[NAME##_di], \
		NAME##_end = cache_record_index(NAME##_first, COUNTS[NAME##_di]), \
		NAME = NAME##_first; \
		NAME != NAME##_end; \
		NAME = cache_record_next(NAME))

#define cache_record_scan_key(NAME, CACHE, KEY) \
	cache_record_scan_context(NAME, CACHE, KEY) \
	cache_record_scan_loop(NAME, KEY, NAME##_ki, NAME##_first, NAME##_rcount)

#define cache_record_scan(NAME, CACHE) \
	cache_record_scan_distributions(NAME, CACHE) \
	cache_record_scan_distribution_records(NAME, CACHE->records, CACHE->counts)

extern inline __attribute__((always_inline))
cache_key_identity_t
cache_default_hash(void *pointer, size_t length)
{
	#if (UINTPTR_MAX == 0xFFFFFFFF)
		return((cache_key_identity_t) hash_32(0, pointer, length));
	#else
		return((cache_key_identity_t) hash_64(0, pointer, length));
	#endif
}

static inline __attribute__((always_inline)) int
cache_key_distribution(cache_storage_t *c, cache_key_t *key)
{
	cache_key_identity_t ki = cache_key_identify(key);
	return(cache_distribution_index(c, ki));
}

static inline __attribute__((always_inline)) cache_record_t
cache_record_previous(cache_record_t r)
{
	return(((void *) r) - cache_record_size());
}

static inline __attribute__((always_inline)) cache_record_t
cache_record_next(cache_record_t r)
{
	return(((void *) r) + cache_record_size());
}

static inline __attribute__((always_inline)) cache_record_t
cache_record_index(cache_record_t r, size_t index)
{
	return(((void *) r) + (cache_record_size() * index));
}

static inline __attribute__((always_inline)) bool
cache_record_usage_threshold(cache_record_t r)
{
	if (r->r_usage.u_hit + r->r_usage.u_missed > CACHE_USAGE_THRESHOLD)
		return(true);

	return(false);
}

/*
	// Bounded increment for usage metrics integers.

	// Only intended for use with &cache_usage_t.u_hit and &cache_usage_t.u_missed as
	// the limit is half of the maximum of a signed type in order to keep sums from
	// overflowing.
*/
#define CACHE_UMETRIC_INCREMENT(X, D) \
	if (CACHE_UMETRIC_LIMIT - X >= (D)) \
		X += (D); \
	else \
		X = CACHE_UMETRIC_LIMIT;

static inline __attribute__((always_inline)) bool
cache_record_hit(cache_record_t r)
{
	CACHE_UMETRIC_INCREMENT(r->r_usage.u_hit, 1)
	return(cache_record_usage_threshold(r));
}

static inline __attribute__((always_inline)) bool
cache_record_miss(cache_record_t r)
{
	CACHE_UMETRIC_INCREMENT(r->r_usage.u_missed, 1)
	return(cache_record_usage_threshold(r));
}

/**
	// The total number of bytes needed to hold a cache record, &cache_record_t.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_record_size(void)
{
	#ifdef CACHE_SOURCE_TEMPLATE
		return(sizeof(struct CacheRecord));
	#else
		return(cache_record_header_size + cache_key_size() + cache_value_size());
	#endif
}

/**
	// Get the pointer to the key held by the record, &r.
*/
CACHE_INTERFACE_QUALIFIERS cache_key_t *
cache_record_key(cache_record_t r)
{
	void *p = (void *) r;
	void *k = p + cache_record_header_size;
	return(k);
}

/**
	// Get the pointer to the value held by the record, &r.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_record_value(cache_record_t r)
{
	void *p = (void *) r;
	void *v = p + cache_record_header_size + cache_key_size();
	return(v);
}

/**
	// Copy the given key, &k, into the record, &r.
	// This does *not* update the key's identity.

	// [ Returns ]
	// The pointer to the key in &r.
*/
CACHE_INTERFACE_QUALIFIERS cache_key_t *
cache_record_set_key(cache_record_t r, cache_key_t *k)
{
	memcpy(cache_record_key(r), k, cache_key_size());
	return(cache_record_key(r));
}

/**
	// Copy the given value, &v, into the record, &r.

	// [ Returns ]
	// The pointer to the value in &r.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_record_set_value(cache_record_t r, cache_value_t *v)
{
	memcpy(cache_record_value(r), v, cache_value_size());
	return(cache_record_value(r));
}

/**
	// Whether the key in the record matches the given key, &k, and its identity, &ki.
*/
CACHE_INTERFACE_QUALIFIERS bool __attribute__((always_inline))
cache_record_matches(cache_record_t r, cache_key_t *k, cache_key_identity_t ki)
{
	if (ki != r->r_identity)
		return(false);

	if (cache_key_compare(cache_record_key(r), k) != 0)
		return(false);

	return(true);
}

/**
	// Move the records' data into the other.
*/
CACHE_INTERFACE_QUALIFIERS void __attribute__((always_inline))
cache_record_swap(cache_record_t r1, cache_record_t r2)
{
	cache_record_t copy_space = alloca(cache_record_size());

	memcpy(copy_space, r1, cache_record_size());
	memcpy(r1, r2, cache_record_size());
	memcpy(r2, copy_space, cache_record_size());
}

/**
	// Copy the key and its identity into the record and reset the usage counters.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t __attribute__((always_inline))
cache_record_initialize(cache_record_t r, cache_key_t *k, cache_key_identity_t ki)
{
	r->r_usage.u_hit = 1;
	r->r_usage.u_missed = 1;
	r->r_usage.u_rate = 1;
	r->r_identity = ki;
	memcpy(cache_record_key(r), k, cache_key_size());
	return(r);
}

/**
	// Change the number of slots in the distribution.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_resize_slots(cache_storage_t *c, size_t di, ssize_t delta)
{
	size_t slots = c->slots[di] + delta;
	size_t size = cache_record_size() * slots;
	cache_record_t records;

	records = (cache_record_t) CACHE_MEMORY_REALLOCATE(c, c->records[di], size);
	if (records == NULL)
		return(c->slots[di]);

	c->slots[di] = slots;
	c->records[di] = records;

	for (size_t i = slots - delta; i < slots; ++i)
		cache_initialize_slot(c, cache_record_index(records, i), di, i);

	return(slots);
}

/**
	// Acquire a slot for record usage.

	// [ Returns ]
	// The pointer to the record with its usage, identity, and key initialized.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_acquire_slot(cache_storage_t *c, int di, cache_key_t *k, cache_key_identity_t ki)
{
	cache_record_t new;
	size_t rcount = c->counts[di];
	size_t slots = c->slots[di];
	cache_record_t records;

	if (rcount >= slots)
	{
		size_t n = cache_resize_slots(c, di, c->allocation_size);
		if (n == slots)
			return(NULL);
	}

	records = c->records[di];
	new = cache_record_index(records, rcount);
	cache_record_initialize(new, k, ki);

	c->counts[di] += 1;
	c->total_record_count += 1;

	return(new);
}

/**
	// Acquire a slot for record usage without acquiring more memory.

	// When the selected distribution is full, the slots at the end of the allocations
	// are reclaimed for use. &cache_evict_record is performed against those
	// reclaimed slots in order to allow the instance to release any associated
	// resources.

	// [ Returns ]
	// The pointer to the record with its usage, identity, and key initialized.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_acquire_slot_fixed(cache_storage_t *c, int di, cache_key_t *k, cache_key_identity_t ki)
{
	cache_record_t new;
	size_t rcount = c->counts[di];
	size_t slots = c->slots[di];
	cache_record_t records = c->records[di];

	// Fixed allocation, reclaim the, presumably, least used records.
	if (rcount >= slots)
	{
		rcount = slots - c->allocation_size;

		c->counts[di] = rcount;
		c->total_record_count -= c->allocation_size;

		// Notify instance of eviction.
		for (size_t i = rcount; i < slots; ++i)
			cache_evict_record(c, cache_record_index(records, i));
	}

	new = cache_record_index(records, rcount);
	cache_record_initialize(new, k, ki);

	c->counts[di] += 1;
	c->total_record_count += 1;

	return(new);
}

/**
	// Analyze the rate and swap the records if the &latter is accessed more often.

	// [ Parameters ]
	// /former/
		// The position to relocate &latter into if accessed more often.
	// /latter/
		// The record whose position is to be reconsidered given
		// a reasonable rate difference.

	// [ Returns ]
	// Pointer to where &latter is now located.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_prioritize_records(cache_record_t former, cache_record_t latter)
{
	cache_umetric_t rd = latter->r_usage.u_rate;

	// Apply decay and take the average old rate with the new.
	rd -= (rd / CACHE_USAGE_RATE_DECAY);
	rd += (latter->r_usage.u_hit / latter->r_usage.u_missed);
	rd /= 2;

	// Clamp rate range to ignore overflow cases.
	if (rd < 0)
		rd = 0;
	else if (rd > CACHE_UMETRIC_LIMIT)
		rd = CACHE_UMETRIC_LIMIT - 1;

	// Reset counters for next threshold.
	latter->r_usage.u_hit = 1;
	latter->r_usage.u_missed = 1;
	latter->r_usage.u_rate = rd;

	// Prioritize more common records, but give former some weight.
	if (rd - former->r_usage.u_rate > CACHE_USAGE_SWAP_MINIMUM)
	{
		cache_record_swap(former, latter);
		return(former);
	}

	return(latter);
}

CACHE_INTERFACE_QUALIFIERS size_t
cache_record_capacity(cache_storage_t *c)
{
	size_t total = 0;

	for (size_t di = 0; di < c->distribution_size; ++di)
		total += c->slots[di];

	return(total);
}

CACHE_INTERFACE_QUALIFIERS size_t
cache_record_count(cache_storage_t *c)
{
	return(c->total_record_count);
}

/**
	// Unconditionally allocate a record associated with the given key.

	// Intended for use when building a cache where the data set is known
	// to not have conflicts.

	// The records are *not* scanned for duplicates.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_insert_record(cache_storage_t *c, cache_key_t *k, cache_value_t *v)
{
	cache_key_identity_t ki = cache_key_identify(k);
	cache_record_t r;

	r = cache_acquire_slot(c, cache_distribution_index(c, ki), k, ki);
	memcpy(cache_record_value(r), v, cache_value_size());

	return(r);
}

/**
	// Find the record with the key, &k.

	// [ Returns ]
	// The record or &NULL if no record with a matching key could be found.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_select_record(cache_storage_t *c, cache_key_t *k)
{
	cache_record_scan_key(r, c, k)
	{
		return(r);
	}

	return(NULL);
}

/**
	// Delete the record identitfied by the key.

	// If found, the record will be swapped with the last record in the distribution and
	// the distribution's record count will be decremented. However, all data within the
	// record will remain in place and can be referenced or updated for any necessary
	// resource maintenance.

	// [ Returns ]
	// The deleted record at its new position in the distribution or &NULL if no
	// match was found.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_delete_record(cache_storage_t *c, cache_key_t *k)
{
	cache_record_scan_key(r, c, k)
	{
		cache_record_t last = cache_record_index(c->records[r_di], c->counts[r_di]-1);
		cache_evict_record(c, r);

		if (last != r)
			cache_record_swap(last, r);

		c->total_record_count -= 1;
		c->counts[r_di] -= 1;

		return(last);
	}

	return(NULL);
}

/**
	// Allocate a record identified by the key, &k, but only if it does not already exists.

	// [ Parameters ]
	// /c/
		// The cache to check.
	// /k/
		// The key to search for.

	// [ Returns ]
	// The allocated record with only the identity being initialized or &NULL if
	// a record with a matching key was found.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_allocate_record(cache_storage_t *c, cache_key_t *k)
{
	cache_record_scan_key(r, c, k)
	{
		// Record with key already exists.
		return(NULL);
	}

	// r_di and r_ki declared by the scan macro.
	return(cache_acquire_slot(c, r_di, k, r_ki));
}

/**
	// Try to find a matching record with the key, &k. If no record can be found,
	// acquire a slot and call the given record initialization function.

	// The scan is performed with &[Prioritization].

	// [ Parameters ]
	// /a/
		// The funciton used to acquire the slot.
		// &cache_acquire_slot when memory allocations are permitted and
		// &cache_acquire_slot_fixed when the least used records should
		// be recycled.
	// /f/
		// The function used to initialize the record if one is allocated
		// due to a miss. When called, the provided record will have its
		// key and identity initialized. The value of the record is not
		// reset and will contain whatever data that was held by the slot.
	// /ctx/
		// The first parameter given to &f if it is called.

	// [ Returns ]
	// The matched record or the acquired slot initialized with &f.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_require_record(cache_storage_t *c, cache_key_t *k, cache_slot_f a, cache_record_f f, void *ctx)
{
	cache_record_scan_key(r, c, k)
	{
		if (cache_record_hit(r))
			return(cache_prioritize_records(r_first, r));
		else
			return(r);
	}
	else
	{
		if (cache_record_miss(r))
			cache_prioritize_records(r_first, r);
		r_first = r;
	}

	// Nothing found, allocate new.
	return(f(ctx, a(c, r_di, k, r_ki)));
}

/**
	// Perform &cache_require_record, and return the record's value.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_require(cache_storage_t *c, cache_key_t *k, cache_slot_f a, cache_record_f f, void *ctx)
{
	return(cache_record_value(cache_require_record(c, k, a, f, ctx)));
}

/**
	// Retrieve the record associated with the key, &k.

	// The scan is performed with &[Prioritization].

	// [ Returns ]
	// The pointer to the matched record, or
	// &NULL if no record with a matching key could be found.
*/
CACHE_INTERFACE_QUALIFIERS cache_record_t
cache_request_record(cache_storage_t *c, cache_key_t *k)
{
	cache_record_scan_key(r, c, k)
	{
		if (cache_record_hit(r))
			return(cache_prioritize_records(r_first, r));
		else
			return(r);
	}
	else
	{
		if (cache_record_miss(r))
			cache_prioritize_records(r_first, r);
		r_first = r;
	}

	// Nothing found.
	return(NULL);
}

/**
	// Retrieve the value associated with the key, &k, using &cache_request_record.

	// The scan is performed with &[Prioritization].

	// [ Returns ]
	// The pointer to the value of the record associated with &k, or
	// &NULL if no record with a matching key could be found.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_request(cache_storage_t *c, cache_key_t *k)
{
	cache_record_t r = cache_request_record(c, k);

	if (r != NULL)
		return(cache_record_value(r));

	// Nothing found.
	return(NULL);
}

/**
	// Retrieve the value associated with the key, &k.

	// [ Returns ]
	// The pointer to the value of the record associated with &k, or
	// &NULL if no record with a matching key could be found.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_get(cache_storage_t *c, cache_key_t *k)
{
	cache_record_scan_key(r, c, k)
	{
		return(cache_record_value(r));
	}

	// No matching record.
	return(NULL);
}

/**
	// Set the value of the record identified by the key, &k, to &v.

	// [ Returns ]
	// The pointer to the value in the record associated with the key or
	// &NULL if a slot could not be acquired.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_set(cache_storage_t *c, cache_key_t *k, cache_value_t *v)
{
	cache_record_t new;

	cache_record_scan_key(r, c, k)
	{
		cache_record_set_value(r, v);
		return(cache_record_value(r));
	}

	// No matching record, acquire a slot with.
	new = cache_acquire_slot(c, r_di, k, r_ki);
	if (new == NULL)
		return(NULL);

	return(cache_record_set_value(new, v));
}

/**
	// Set default. Allocate a new record initialized with the given key and value,
	// but only if there are no records with a matching key.

	// [ Returns ]
	// If a matching record is found, the value of the existing record is returned.
	// If a new slot is acquired, the record will be initialized and its value is returned.
	// Otherwise, &NULL if the record did not exist and a slot could not be acquired due to
	// memory allocation failure.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_default(cache_storage_t *c, cache_key_t *k, cache_value_t *v)
{
	cache_record_t new;

	cache_record_scan_key(r, c, k)
	{
		// Key is present, nothing to do.
		return(cache_record_value(r));
	}

	new = cache_acquire_slot(c, r_di, k, r_ki);
	if (new == NULL)
		return(NULL);

	return(cache_record_set_value(new, v));
}

/**
	// Find the record with the given key and update its value.

	// [ Returns ]
	// The pointer to the value in the matching record or
	// &NULL if no record with a matching key could be found.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_update(cache_storage_t *c, cache_key_t *k, cache_value_t *v)
{
	cache_record_scan_key(r, c, k)
	{
		return(cache_record_set_value(r, v));
	}

	return(NULL);
}

/**
	// Delete the record matched by the key, &k, in &c.

	// If the key in the stored record is needed, &cache_delete_record
	// should be used.

	// [ Returns ]
	// The pointer to the value in the deleted record or
	// &NULL if no record with a matching key could be found.
*/
CACHE_INTERFACE_QUALIFIERS cache_value_t *
cache_delete(cache_storage_t *c, cache_key_t *k)
{
	cache_record_t r;
	r = cache_delete_record(c, k);
	if (r == NULL)
		return(NULL);
	return(cache_record_value(r));
}

/**
	// Copy records from &src into &dst, but only the keys that are present in &dst.

	// [ Parameters ]
	// /dst/
		// The destination cache.
	// /src/
		// The source cache.

	// [ Returns ]
	// The number updated.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_update_records(cache_storage_t *dst, cache_storage_t *src)
{
	size_t rchanged = 0;

	for (size_t i = 0; i < src->distribution_size; ++i)
	{
		size_t count = src->counts[i];
		cache_record_t records = src->records[i];

		for (size_t ri = 0; ri < count; ++ri)
		{
			cache_record_t dr, sr = cache_record_index(records, ri);

			if (sr->r_identity == 0) // Deleted record.
				continue;

			dr = cache_select_record(dst, cache_record_key(sr));
			if (dr == NULL)
				continue;

			memcpy(cache_record_key(dr), cache_record_key(sr), cache_key_size() + cache_value_size());
			rchanged += 1;
		}
	}

	return(rchanged);
}

/**
	// Copy records from &src into &dst, but only when the key is not present in &dst.

	// [ Parameters ]
	// /dst/
		// The destination cache.
	// /src/
		// The source cache.

	// [ Returns ]
	// The number updated.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_extend_records(cache_storage_t *dst, cache_storage_t *src)
{
	size_t rchanged = 0;

	for (size_t i = 0; i < src->distribution_size; ++i)
	{
		size_t count = src->counts[i];
		cache_record_t records = src->records[i];

		for (size_t ri = 0; ri < count; ++ri)
		{
			cache_record_t dr, sr = cache_record_index(records, ri);

			if (sr->r_identity == 0) // Deleted record.
				continue;

			dr = cache_allocate_record(dst, cache_record_key(sr));
			if (dr == NULL)
				continue;

			memcpy(cache_record_key(dr), cache_record_key(sr), cache_key_size() + cache_value_size());
			rchanged += 1;
		}
	}

	return(rchanged);
}

/**
	// Copy all records from &src to &dst replacing any that already exist.
	// This is equivalent to performing both &cache_update_records and
	// &cache_extend_records.

	// [ Parameters ]
	// /dst/
		// The destination cache.
	// /src/
		// The source cache.

	// [ Returns ]
	// The number copied.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_replace_records(cache_storage_t *dst, cache_storage_t *src)
{
	size_t rchanged = 0;

	for (size_t i = 0; i < src->distribution_size; ++i)
	{
		size_t count = src->counts[i];
		cache_record_t records = src->records[i];

		for (size_t ri = 0; ri < count; ++ri)
		{
			cache_record_t dr, sr = cache_record_index(records, ri);

			dr = cache_select_record(dst, cache_record_key(sr));
			if (dr != NULL)
				memcpy(cache_record_value(dr), cache_record_value(sr), cache_value_size());
			else
				dr = cache_insert_record(dst, cache_record_key(sr), cache_record_value(sr));

			rchanged += 1;
		}
	}

	return(rchanged);
}

/**
	// Remove records in &dst when their keys also exist in &src.

	// [ Parameters ]
	// /dst/
		// The cache whose records will be removed.
	// /src/
		// The cache holding the keys that should be removed from &dst.

	// [ Returns ]
	// The number deleted.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_discard_records(cache_storage_t *dst, cache_storage_t *src)
{
	size_t rchanged = 0;

	cache_record_scan(r, src)
	{
		cache_record_t dr = cache_delete_record(dst, cache_record_key(r));
		if (dr != NULL)
			++rchanged;
	}

	return(rchanged);
}

/**
	// Delete all records from the cache that are stored in the specified
	// distributions, &dstart to &dstop.

	// &cache_evict_record will be called for each record removed.

	// [ Returns ]
	// Number of records removed.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_truncate_distributions(cache_storage_t *c, size_t dstart, size_t dstop)
{
	size_t ndeleted = 0;

	// Zero record counts after evicting.
	for (size_t i = dstart; i < dstop; ++i)
	{
		cache_record_t r = c->records[i];
		size_t n = c->counts[i];

		ndeleted += n;
		c->total_record_count -= n;
		c->counts[i] = 0;

		for (size_t j = 0; j < n; ++j)
			cache_evict_record(c, cache_record_index(r, j));
	}

	return(ndeleted);
}

/**
	// Delete all records from the cache.

	// &cache_evict_record will be called for each record removed.

	// [ Returns ]
	// Number of records removed.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_truncate_records(cache_storage_t *c)
{
	return(cache_truncate_distributions(c, 0, c->distribution_size));
}

/**
	// Call the function, &f, for each record in the cache.

	// [ Returns ]
	// Number of records scanned.
*/
CACHE_INTERFACE_QUALIFIERS size_t
cache_scan_records(cache_storage_t *c, cache_record_f f, void *ctx)
{
	size_t n = 0;

	cache_record_scan(r, c)
	{
		f(ctx, r);
		++n;
	}

	return(n);
}

/**
	// Redistribute the cache's records to the new size.

	// A new cache is initialized during the transfer that will replace
	// the cache's, &c, configuration and allocations once complete.

	// [ Returns ]
	// Zero on success, non-zero on memory allocation failure, &cache_initialize.
*/
CACHE_INTERFACE_QUALIFIERS int
cache_redistribute_records(cache_storage_t *c, size_t distribution_size)
{
	cache_storage_t rc;
	size_t r, sets = 0;

	// Identify the approximate initial factor for the new size.
	sets = (c->total_record_count / distribution_size) / c->allocation_size;

	r = cache_initialize(&rc, distribution_size, c->allocation_size, sets + 1);
	if (r != 0)
		return(r);

	cache_record_scan(r, c)
	{
		cache_insert_record(&rc, cache_record_key(r), cache_record_value(r));
	}

	cache_release(c);
	memcpy(c, &rc, sizeof(rc));
	return(0);
}

/**
	// Free any memory allocations held by the cache.
*/
CACHE_INTERFACE_QUALIFIERS void
cache_release(cache_storage_t *c)
{
	if (c->counts != NULL)
	{
		CACHE_MEMORY_RELEASE(c, c->counts);
		c->counts = NULL;
	}

	if (c->slots != NULL)
	{
		CACHE_MEMORY_RELEASE(c, c->slots);
		c->slots = NULL;
	}

	if (c->records != NULL)
	{
		for (int i = 0; i < c->distribution_size; ++i)
		{
			if (c->records[i] != NULL)
				CACHE_MEMORY_RELEASE(c, c->records[i]);
		}

		CACHE_MEMORY_RELEASE(c, c->records);
		c->records = NULL;
	}
}

/**
	// Configure &c.allocation_size,
	// &c.distribution_size and allocate memory for the records.

	// [ Parameters ]
	// /c/
		// The cache storage to initialize.
	// /dsize/
		// The &cache_storage_t.distribution_size to configure.
	// /asize/
		// The &cache_storage_t.allocation_size to configure.
	// /afactor/
		// The multiple to use when allocating the first record slots
		// for the distributions.
		// `c->records[i] = malloc(record_size() * asize * afactor)`
*/
CACHE_INTERFACE_QUALIFIERS int
cache_initialize(cache_storage_t *c, size_t dsize, size_t asize, size_t afactor)
{
	size_t rasize, sasize, rssize;

	if (!asize || !dsize || !afactor)
		return(-2);

	c->distribution_size = dsize;
	c->allocation_size = asize;
	c->total_record_count = 0;

	sasize = sizeof(size_t) * c->distribution_size;
	rssize = sizeof(void *) * c->distribution_size;

	c->records = (cache_record_t *) CACHE_MEMORY_ALLOCATE(c, rssize);
	if (c->records == NULL)
		return(-1);
	// Zero the records pointers for &cache_release.
	memset((void *) c->records, 0, rssize);

	c->counts = CACHE_MEMORY_ALLOCATE(c, sasize);
	c->slots = CACHE_MEMORY_ALLOCATE(c, sasize);
	if (c->counts == NULL || c->slots == NULL)
	{
		cache_release(c);
		return(-1);
	}

	memset(c->counts, 0, sasize);
	rasize = cache_record_size() * c->allocation_size * afactor;
	for (size_t i = 0; i < c->distribution_size; ++i)
	{
		size_t slots = c->allocation_size * afactor;
		cache_record_t rs;

		rs = (cache_record_t) CACHE_MEMORY_ALLOCATE(c, rasize);
		if (rs == NULL)
		{
			c->records[i] = NULL;
			c->slots[i] = 0;
			cache_release(c);
			return(-1);
		}
		c->records[i] = rs;
		c->slots[i] = slots;

		for (size_t j = 0; j < slots; ++j)
			cache_initialize_slot(c, cache_record_index(rs, j), i, j);
	}

	return(0);
}

/**
	// Whether the cache is ready for use.
*/
CACHE_INTERFACE_QUALIFIERS bool
cache_initialized(cache_storage_t *c)
{
	if (c == NULL)
		return(false);
	return(c->counts != NULL && c->slots != NULL && c->records != NULL);
}

/**
	// Allocate, &malloc, and &cache_initialize a &cache_storage_t.
*/
CACHE_INTERFACE_QUALIFIERS cache_storage_t *
cache_create(size_t dsize, size_t asize, size_t afactor)
{
	cache_storage_t *c = malloc(sizeof(cache_storage_t));
	if (c == NULL)
		return(NULL);

	if (cache_initialize(c, dsize, asize, afactor))
	{
		free(c);
		return(NULL);
	}

	return(c);
}

/**
	// &cache_release and free, &free, the given cache.
*/
CACHE_INTERFACE_QUALIFIERS void
cache_destroy(cache_storage_t *c)
{
	cache_release(c);
	free(c);
}
