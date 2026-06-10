#ifndef _FAULT_STATUS_H_
#define _FAULT_STATUS_H_

#include "status/context.h"

#ifndef STF_API
	#define STF_API(TYPE) TYPE
#endif

#ifndef STF_ISI
	#define STF_ISI(TYPE) extern inline TYPE
#endif

#include "status/prototypes.h"
#endif
