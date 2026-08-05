#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <limits.h>
#include <fault/hash.h>

/**
	// Macro to disable qualifiers that cause malfunctions under gcc.

	// When a source level template is not in play, the `inline` specifier
	// is often not desired under gcc as it will inline the weak functions
	// locally in `cache.c`. After linking with the overrides, some of the
	// default behaviors remain and lead to corruption if used. Additionally,
	// some non-weak functions will trigger errors if marked always inline.
*/
#if defined(__GNUC__) && !defined(__clang__)
	#define CACHE_GCC_UNSUPPORTED(X)
#else
	#define CACHE_GCC_UNSUPPORTED(X) X
#endif
