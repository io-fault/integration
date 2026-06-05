/**
	// UTF-8 decoding and encoding tools.
*/
#ifndef _FAULT_UTF_8_H_
#define _FAULT_UTF_8_H_

/**
	// Visibility and linkage control define for the primary interfaces.
*/
#ifndef UTF8_API
	#define UTF8_API(TYPE) TYPE
#endif

/**
	// Visibility and linkage control define for a few internal functions.
*/
#ifndef UTF8_ISI
	#define UTF8_ISI(TYPE) static inline TYPE
#endif

#include "utf-8/context.h"
#include "utf-8/prototypes.h"
#endif
