/**
	// Defines adjusting symbol names and storage qualifiers for prototypes.
*/

#ifndef CACHE_SYMBOL
	/**
		// Cache interface name.
	*/
	#define CACHE_SYMBOL(NAME) cache_##NAME
#endif

#ifndef CACHE_PARAMETER_QUALIFIERS
	/**
		// Attributes needed by the instance functions.
	*/
	//#define CACHE_PARAMETER_QUALIFIERS __attribute__((always_inline))
	#define CACHE_PARAMETER_QUALIFIERS
#endif

#ifndef CACHE_INTERFACE_QUALIFIERS
	/**
		// Attributes for the primary interfaces needed by the instance.
	*/
	//#define CACHE_INTERFACE_QUALIFIERS __attribute__((always_inline))
	#define CACHE_INTERFACE_QUALIFIERS
#endif

#ifndef CACHE_USAGE_THRESHOLD
	/**
		// Sum of hit and miss needed for considering the prioritization of a record.
	*/
	#define CACHE_USAGE_THRESHOLD 32
#endif

#ifndef CACHE_USAGE_SWAP_MINIMUM
	/**
		// The rate difference required to cause a record swap.
	*/
	#define CACHE_USAGE_SWAP_MINIMUM (CACHE_USAGE_THRESHOLD / 2)
#endif

#ifndef CACHE_USAGE_RATE_DECAY
	/**
		// The fraction of the rate that should be maintained across usage
		// thresholds. Expressed as a whole number used as the divisor.
	*/
	#define CACHE_USAGE_RATE_DECAY (CACHE_USAGE_THRESHOLD)
#endif

#ifndef CACHE_MEMORY_ALLOCATE
	/**
		// Allocate memory with respect to a cache. Defaults to &malloc.
	*/
	#define CACHE_MEMORY_ALLOCATE(C, S) malloc(S)
#endif

#ifndef CACHE_MEMORY_REALLOCATE
	/**
		// Reallocate memory with respect to a cache. Defaults to &realloc.
	*/
	#define CACHE_MEMORY_REALLOCATE(C, P, S) realloc(P, S)
#endif

#ifndef CACHE_MEMORY_RELEASE(C, S)
	/**
		// Release allocated memory with respect to a cache. Defaults to &free.
	*/
	#define CACHE_MEMORY_RELEASE(C, S) free(S)
#endif
