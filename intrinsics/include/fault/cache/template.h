#define CACHE_SOURCE_TEMPLATE
// context.h or equivalent must be provided by the TU.
#include "control.h"
#include "types.h"

typedef struct CacheStorage cache_storage_t;
typedef struct CacheRecord *cache_record_t;

/**
	// Turn the filtering on for the prototypes.
*/
#if defined(__GNUC__) && !defined(__clang__)
	#define CACHE_GCC_UNSUPPORTED(X)
#else
	#define CACHE_GCC_UNSUPPORTED(X) X
#endif

#include "parameters.h"
#include "interfaces.h"
#include "prototypes.h"

#define CACHE_GCC_UNSUPPORTED(X) X

#include "implementation.c"
