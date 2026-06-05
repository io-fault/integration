#ifndef _FAULT_BASE_64_H_
#define _FAULT_BASE_64_H_

#include <assert.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <setjmp.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <inttypes.h>
#include <wchar.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/uio.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/resource.h>

// API (can be static inline or exported)
#ifndef BASE64_API
	#define BASE64_API(TYPE) TYPE
#endif

// Internal Interfaces (should be static inline)
#ifndef BASE64_ISI
	#define BASE64_ISI(TYPE) static inline TYPE
#endif

#include "base-64/context.h"
#include "base-64/prototypes.h"
#endif
