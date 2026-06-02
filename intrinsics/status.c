/**
	// TTYN.1 Status Frames.
*/
#ifndef _FAULT_STATUS_H_
#define _FAULT_STATUS_H_

#define STF_PROTOCOL "http://fault.io/protocol/status/frames"

/**
	// UTF-8, encouraged, string type.
*/
typedef const uint8_t * stf_string_t;
const static stf_string_t stf_protocol = (stf_string_t) STF_PROTOCOL;
const static stf_string_t stf_protocol_ttyn1_declaration = (stf_string_t)
	"[!? PROTOCOL: " STF_PROTOCOL " tty-notation-1]";

#define _STF_REFLECT(...) __VA_ARGS__
#define _STF_VOID(...)

#ifndef STF_API
	#define STF_API(TYPE) static TYPE
#endif

#ifndef STF_ISI
	#define STF_ISI(TYPE) static inline TYPE
#endif

#ifndef STF_MALLOC
	#define STF_MALLOC(S) malloc(S)
#endif
#ifndef STF_REALLOC
	#define STF_REALLOC(P, S) realloc(P, S)
#endif
#ifndef STF_FREE
	#define STF_FREE(P) free(P)
#endif

#ifndef STF_CLOCK_TIMESTAMP
	#define STF_CLOCK_TIMESTAMP() clock_view_time((clock_view_t *const) &y2k1_us_clock)
#endif

#ifndef STF_CLOCK_ELAPSED
	#define STF_CLOCK_ELAPSED() clock_view_elapsed((clock_view_t *const) &y2k1_ns_clock)
#endif

/**
	// Frame type list.
*/
#define STF_EVENTS(EVENT_TYPE) \
	EVENT_TYPE("!", "?", message, protocol) \
	EVENT_TYPE("!", "&", reference) \
	EVENT_TYPE(">", "<", transaction, failed) \
	EVENT_TYPE("<", ">", transaction, executed) \
	EVENT_TYPE("-", ">", transaction, started) \
	EVENT_TYPE("-", "-", transaction, event) \
	EVENT_TYPE("<", "-", transaction, stopped) \
	EVENT_TYPE("!", "#", message, application) \
	EVENT_TYPE("!", "*", message, framework) \
	EVENT_TYPE("!", "~", message, trace) \
	EVENT_TYPE("!", "%", message, administrative) \
	EVENT_TYPE("!", ">", message, entity) \
	EVENT_TYPE("+", "=", elements, inserted) \
	EVENT_TYPE("-", "=", elements, deleted) \
	EVENT_TYPE("Δ", "=", elements, delta) \
	EVENT_TYPE("<", "=", elements, reverted) \
	EVENT_TYPE("=", "=", elements, committed) \
	EVENT_TYPE("+", ".", resource, initialized) \
	EVENT_TYPE("-", ".", resource, deleted) \
	EVENT_TYPE("±", ".", resource, relocated) \
	EVENT_TYPE("*", ".", resource, replicated) \
	EVENT_TYPE("&", ".", resource, referenced) \
	EVENT_TYPE("=", ".", resource, rewritten) \
	EVENT_TYPE("Δ", ".", resource, delta) \
	EVENT_TYPE("^", "*", archive, extraction, replicated) \
	EVENT_TYPE("^", "+", archive, extraction, replicated, merge) \
	EVENT_TYPE("√", "*", archive, delta, replicated, into) \
	EVENT_TYPE("√", "+", archive, delta, merged, into) \
	EVENT_TYPE("√", "-", archive, delta, deleted) \
	EVENT_TYPE("√", "&", archive, delta, referenced) \
	EVENT_TYPE("↑", ".", resource, transmitted) \
	EVENT_TYPE("↓", ".", resource, received) \
	EVENT_TYPE("↑", ":", data, transmitted) \
	EVENT_TYPE("↓", ":", data, received) \
	EVENT_TYPE("↓", "↑", data, transferred)

/**
	// Supporting boilerplate for STF_EVENTS() access.
*/
#if 1
	// String identifier catenation. (enum support)
	#define _STF_SYMBOL_STRING_6(S1) #S1
	#define _STF_SYMBOL_STRING_5(S1, ...) \
		#S1 __VA_OPT__("-") __VA_OPT__(_STF_SYMBOL_STRING_6(__VA_ARGS__))
	#define _STF_SYMBOL_STRING_4(S1, ...) \
		#S1 __VA_OPT__("-") __VA_OPT__(_STF_SYMBOL_STRING_5(__VA_ARGS__))
	#define _STF_SYMBOL_STRING_3(S1, ...) \
		#S1 __VA_OPT__("-") __VA_OPT__(_STF_SYMBOL_STRING_4(__VA_ARGS__))
	#define _STF_SYMBOL_STRING_2(S1, ...) \
		#S1 __VA_OPT__("-") __VA_OPT__(_STF_SYMBOL_STRING_3(__VA_ARGS__))
	#define _STF_SYMBOL_STRING_1(S1, ...) \
		#S1 __VA_OPT__("-") __VA_OPT__(_STF_SYMBOL_STRING_2(__VA_ARGS__))
	#define STF_EVENT_TYPE_SYMBOL_STRING(...) _STF_SYMBOL_STRING_1(__VA_ARGS__)

	// C identifier catenation. (EStruct.symbol representation)
	#define _STF_SYMBOL_IDENTIFIER_6(S1,S2,S3,S4,S5,S6,...) \
		S1##_##S2##_##S3##_##S4##_##S5##_##S6
	#define _STF_SYMBOL_IDENTIFIER_5(S1,S2,S3,S4,S5,...) \
		S1##_##S2##_##S3##_##S4##_##S5
	#define _STF_SYMBOL_IDENTIFIER_4(S1,S2,S3,S4,...) \
		S1##_##S2##_##S3##_##S4
	#define _STF_SYMBOL_IDENTIFIER_3(S1,S2,S3,...) \
		S1##_##S2##_##S3
	#define _STF_SYMBOL_IDENTIFIER_2(S1,S2,...) \
		S1##_##S2
	#define _STF_SYMBOL_IDENTIFIER_1(S1,...) \
		S1

	// Limited variant of argument counting.
	#define _STF_SYMBOL_IDENTIFIER_SET() \
		_STF_SYMBOL_IDENTIFIER_5, \
		_STF_SYMBOL_IDENTIFIER_4, \
		_STF_SYMBOL_IDENTIFIER_3, \
		_STF_SYMBOL_IDENTIFIER_2, \
		_STF_SYMBOL_IDENTIFIER_1
	#define _STF_SYMBOL_IDENTIFIER_SELECT(_1,_2,_3,_4,_5,N,...) N
	#define _STF_SYMBOL_IDENTIFIER(SELECTION, ...) SELECTION(__VA_ARGS__)

	#define _STF_EVENT_TYPE_SYMID(...) \
		_STF_SYMBOL_IDENTIFIER(_STF_SYMBOL_IDENTIFIER_SELECT(__VA_ARGS__), __VA_ARGS__)

	// Level of indirection needed to resolve the _STF_SYMBOL_IDENTIFIER call.
	#define _STF_CAT_L1(A,B,C) _STF_CAT_3(A,B,C)
	#define _STF_CAT_3(A,B,C) A##B##C

	#define _STF_EVENT_TYPE_SYMBOL_IDENTIFIER(...) \
		_STF_EVENT_TYPE_SYMID(__VA_ARGS__, _STF_SYMBOL_IDENTIFIER_SET())

	#define _STF_LCHRVAL(C) ((L##C)[0])
#endif

#define STF_EVENT_TYPE_SYMBOL_COMPOSE(PREFIX, SUFFIX, ...) \
	_STF_CAT_L1(PREFIX, _STF_EVENT_TYPE_SYMBOL_IDENTIFIER(__VA_ARGS__), SUFFIX)
#define STF_EVENT_TYPE_CODE(F, L) ( (_STF_LCHRVAL(F) << 16) | (_STF_LCHRVAL(L)) )

/**
	// Enumeration of the &STF_EVENTS table.

	// Provides access to frame type codes using the event's symbol.
*/
enum EFrameType {
	#define D(T1, T2, ...) \
		STF_EVENT_TYPE_SYMBOL_COMPOSE(stf_, _event, __VA_ARGS__) = \
			STF_EVENT_TYPE_CODE(T1, T2),

		STF_EVENTS(D)
	#undef D
};

STF_ISI(size_t)
_stf_calculate_type_code(uint8_t *buffer, uint32_t code)
{
	size_t seqlen = 0;

	seqlen += utf8_sequence_codepoint(buffer, code >> 16);
	seqlen += utf8_sequence_codepoint(buffer + seqlen, code & 0xFFFF);
	return(seqlen);
}

/**
	// Get the frame type identifier ("?!") from the given code using
	// a lookup table built from &STF_EVENTS.

	// [ Returns ]
	// The associated type identifier or "??" if unrecognized.
*/
STF_ISI(stf_string_t)
stf_type_identifier(int64_t code)
{
	switch (code)
	{
		#define ET(TID1, TID2, ...) \
			case STF_EVENT_TYPE_CODE(TID1, TID2): \
				return((stf_string_t) TID1 TID2); \
			break;
			STF_EVENTS(ET)
		#undef ET

		default:
		break;
	}

	return((stf_string_t) "??");
}

/**
	// Get the frame type symbol ("elements-inserted") from the given code using
	// a lookup table built from &STF_EVENTS.

	// [ Returns ]
	// The dash separated identifier string associated with the type code or
	// `"unrecognized-frame-type"` if the code is not recognized.
*/
STF_ISI(stf_string_t)
stf_type_symbol(int64_t code)
{
	switch (code)
	{
		#define ET(TID1, TID2, ...) \
			case STF_EVENT_TYPE_CODE(TID1, TID2): \
				return((stf_string_t) STF_EVENT_TYPE_SYMBOL_STRING(__VA_ARGS__)); \
			break;
			STF_EVENTS(ET)
		#undef ET

		default:
		break;
	}

	return((stf_string_t) "unrecognized-frame-type");
}

/**
	// Field table for &EStruct.

	// Records are strangely classified to accommodate various needs.
*/
#define ESTRUCT_FIELDS(CONTEXT, RENAME, FSTRC, FSTRT, FINTS, FLAST) \
	FSTRC(CONTEXT, 1, RENAME(protocol), stf_string_t) \
	FINTS(CONTEXT, 2, RENAME(code), int64_t) \
	FSTRT(CONTEXT, 3, RENAME(identifier), stf_string_t) \
	FSTRT(CONTEXT, 4, RENAME(symbol), stf_string_t) \
	FLAST(CONTEXT, 5, RENAME(abstract), stf_string_t)

#define _ESTRUCT_PARAMETERS(CONTEXT, INDEX, NAME, TYPE) \
	TYPE NAME,
#define _ESTRUCT_PARAMETERS_FINAL(CONTEXT, INDEX, NAME, TYPE) \
	TYPE NAME
#define _ESTRUCT_FIELDS_C(CFIELD) \
	ESTRUCT_FIELDS(void, _STF_REFLECT, CFIELD, CFIELD, CFIELD, CFIELD)
#define _ESTRUCT_FIELDS_S(CFIELD) \
	ESTRUCT_FIELDS(void, _STF_REFLECT, _STF_VOID, CFIELD, _STF_VOID, CFIELD)
#define _ESTRUCT_FIELDS_I(CFIELD) \
	ESTRUCT_FIELDS(void, _STF_REFLECT, _STF_VOID, _STF_VOID, CFIELD, _STF_VOID)
#define _ESTRUCT_FIELD_INDEX(NAME) stf_event_##NAME##_fi

/**
	// Formulate ESTRUCT_FIELDS() suitable for function parameters.
*/
#define _ESTRUCT_FMT_S(CONTEXT, INDEX, NAME, TYPE) #CONTEXT #NAME #NAME ": %s"
#define _ESTRUCT_FMT_I(CONTEXT, INDEX, NAME, TYPE) #CONTEXT #NAME #NAME ": " PRId64

#define _ESTRUCT_SELECT_ITEM(CONTEXT, INDEX, NAME, TYPE) CONTEXT->NAME,
#define _ESTRUCT_SELECT_LAST(CONTEXT, INDEX, NAME, TYPE) CONTEXT->NAME

#define stf_event_formatting(...) \
	ESTRUCT_FIELDS(_STF_VOID(), _STF_REFLECT, \
		_ESTRUCT_FMT_S, \
		_ESTRUCT_FMT_S, \
		_ESTRUCT_FMT_I, \
		_ESTRUCT_FMT_S)
#define stf_event_select_fields(VAR) \
	ESTRUCT_FIELDS(VAR, _STF_REFLECT, \
		_ESTRUCT_SELECT_ITEM, \
		_ESTRUCT_SELECT_ITEM, \
		_ESTRUCT_SELECT_ITEM, \
		_ESTRUCT_SELECT_LAST)

/**
	// Construct an argument list from the EStruct fields with
	// prefixed names.
*/
#define stf_event_arguments_l(PREFIX) \
	ESTRUCT_FIELDS(PREFIX, _STF_REFLECT, \
		_ESTRUCT_SELECT_ITEM, \
		_ESTRUCT_SELECT_ITEM, \
		_ESTRUCT_SELECT_ITEM, \
		_ESTRUCT_SELECT_LAST)

/**
	// Construct a parameter list from the EStruct fields with
	// prefixed names.
*/
#define stf_event_parameters_l(PREFIX) \
	ESTRUCT_FIELDS(PREFIX, _STF_REFLECT, \
		_ESTRUCT_PARAMETERS, \
		_ESTRUCT_PARAMETERS, \
		_ESTRUCT_PARAMETERS, \
		_ESTRUCT_PARAMETERS_FINAL)

/**
	// Construct an argument list from the EStruct fields.
*/
#define stf_event_arguments stf_event_arguments_l(_STF_VOID())

/**
	// Construct a parameter list from the EStruct fields.
*/
#define stf_event_parameters stf_event_parameters_l(_STF_VOID())

struct EStruct {
	#define DEF(CONTEXT, INDEX, NAME, TYPE) TYPE NAME;
		_ESTRUCT_FIELDS_C(DEF)
	#undef DEF
};

/**
	// Event structure identifying the type of status event and summary message
	// regarding the particular instance.

	// [ Elements ]
	// /protocol/
		// The, usually constant, string identifying the set of possible events.
	// /code/
		// The integer code identifying the event type.
	// /identifier/
		// The string identifier of the event type.
	// /symbol/
		// The string name used to reference the event.
	// /abstract/
		// Summary description of the event or error.
*/
typedef struct EStruct stf_event_t;

struct StatusFrame {
	stf_string_t sf_channel;
	stf_string_t sf_extension_data;
	size_t sf_extension_length;

	stf_event_t sf_type;
};

/**
	// Status event with attached data extension and associated channel.

	// [ Elements ]
	// /sf_channel/
		// The subdivision of the frame transport to aid in routing if needed.
		// Normally unused.
	// /sf_extension_length/
		// The number of bytes in &sf_extension_data that should be considered
		// for use.
	// /sf_extension_data/
		// The data attached to the frame providing greater detail
		// and context about the event.
	// /sf_type/
		// The event type of the frame. Placed at the end to allow a full
		// EStructAllocation to be used.
*/
typedef struct StatusFrame stf_message_t;

enum EStructFieldIndex {
	stf_event_void_fi = 0,

	#define DEF(CONTEXT, INDEX, NAME, TYPE) \
		_ESTRUCT_FIELD_INDEX(NAME) = INDEX,

		_ESTRUCT_FIELDS_C(DEF)
	#undef DEF

	stf_event_sentinel_fi
};

/**
	// Field index references, `stf_event_FIELDNAME_fi`.
*/
typedef enum EStructFieldIndex stf_event_field_t;

/**
	// Single allocation &EStruct.
	// An &EStruct with string lengths and attached string storage.
*/
struct EStructAllocation {
	struct EStruct esa_fields;
	uint16_t esa_string_lengths[3];
	uint8_t esa_string_storage[1];
};

/**
	// Calculates the additional storage required to integrate the event.
*/
STF_API(size_t)
stf_size_event(struct EStructAllocation *esa, stf_event_parameters)
{
	size_t st_length = 0;

	esa->esa_fields.code = 0;
	esa->esa_string_storage[0] = 0;

	st_length += esa->esa_string_lengths[0] = strlen((const char *) identifier);
	st_length += esa->esa_string_lengths[1] = strlen((const char *) symbol);
	st_length += esa->esa_string_lengths[2] = strlen((const char *) abstract);

	st_length += sizeof(esa->esa_string_lengths) / sizeof(uint16_t); // NULs

	return(st_length);
}

/**
	// Update the EStruct pointers after a memory move to reflect the new positions.

	// &stf_event_t.protocol is expected to be consistent.

	// [ Returns ]
	// Pointer (identical) to &esa as a &stf_event_t.
*/
STF_API(stf_event_t *)
stf_update_storage(struct EStructAllocation *esa)
{
	size_t st_length = sizeof(*esa);
	size_t offsets[3];

	offsets[0] = st_length + 1;
	offsets[1] = offsets[0] + esa->esa_string_lengths[0] + 1;
	offsets[2] = offsets[1] + esa->esa_string_lengths[1] + 1;

	esa->esa_fields.identifier = (stf_string_t) esa + offsets[0];
	esa->esa_fields.symbol = (stf_string_t) esa + offsets[1];
	esa->esa_fields.abstract = (stf_string_t) esa + offsets[2];
}

/**
	// Copy the given event parameters into &esa.

	// [ Returns ]
	// Pointer (identical) to &esa as a &stf_event_t.
*/
STF_API(stf_event_t *)
stf_integrate_event(struct EStructAllocation *esa, stf_event_parameters)
{
	int idx;

	esa->esa_fields.protocol = protocol;
	esa->esa_fields.code = code;

	#define _FSETS(CONTEXT, INDEX, NAME, TYPE) \
		strncpy((char *) esa->esa_fields.NAME, (const char *) NAME, \
			esa->esa_string_lengths[INDEX-3]+1);

		_ESTRUCT_FIELDS_S(_FSETS)
	#undef _FSETS

	return((struct EStruct *) esa);
}

/**
	// Allocate and initialize an &stf_event_t.

	// [ Returns ]
	// Single &STF_MALLOC allocation holding a copy of the given parameters.
*/
STF_API(stf_event_t *)
stf_construct_event(stf_event_parameters)
{
	size_t st_length = sizeof(struct EStructAllocation);
	uint16_t sfsizes[3];
	struct EStructAllocation *ftype;

	st_length += sfsizes[0] = strlen((const char *) identifier);
	st_length += sfsizes[1] = strlen((const char *) symbol);
	st_length += sfsizes[2] = strlen((const char *) abstract);

	st_length += sizeof(sfsizes) / sizeof(uint16_t); // NULs

	ftype = (struct EStructAllocation *) STF_MALLOC(st_length);

	ftype->esa_fields.protocol = protocol;
	ftype->esa_fields.code = code;
	ftype->esa_string_storage[0] = 0;

	ftype->esa_fields.identifier = (stf_string_t)
		ftype + sizeof(struct EStructAllocation) + 1;
	ftype->esa_fields.symbol = (stf_string_t)
		ftype + sizeof(struct EStructAllocation) + 2 + sfsizes[0];
	ftype->esa_fields.abstract = (stf_string_t)
		ftype + sizeof(struct EStructAllocation) + 3 + sfsizes[0] + sfsizes[1];

	// Copy stf_event string arguments.
	#define _FSETS(CONTEXT, INDEX, NAME, TYPE) \
		strcpy((char *) ftype->esa_fields.NAME, (const char *) NAME);

		_ESTRUCT_FIELDS_S(_FSETS)
	#undef _FSETS

	return((struct EStruct *) ftype);
}

/**
	// Compare all of the fields of the two event types.

	// [ Returns ]
	// Zero when the data in all of the fields are identical.
	// Otherwise, the index of the fields that differ.
*/
STF_API(stf_event_field_t)
stf_event_compare(stf_event_t *op1, stf_event_t *op2)
{
	if (op1->protocol != op2->protocol)
		return(stf_event_protocol_fi);
	if (op1->code != op2->code)
		return(stf_event_code_fi);

	#define _FCMP(CONTEXT, INDEX, NAME, TYPE) \
		if (strcmp((const char *) op1->NAME, (const char *) op2->NAME)) \
			return((stf_event_field_t) INDEX);

		_ESTRUCT_FIELDS_S(_FCMP)
	#undef _FCMP

	return(stf_event_void_fi);
}

/**
	// Formatting constants used for TTYN.1 status frames.

	// /TTYN1_SIGNATURE/
		// The OSC sequence declaring the status frame.
		// Used to determine whether extension data should be checked for.
	// /TTYN1_OPEN/
		// The opening sequence for the extension data URL.
	// /TTYN1_CLOSE_URL/
		// OSC 8 close sequence configuring the URL.
	// /TTYN1_RESET_URL/
		// OSC 8 closing the linked text.
	// /TTYN1_DATA_URL/
		// Default data URL prefix.
*/
#define TTYN1_SIGNATURE "\x1b]\x03\x1b\\"
#define TTYN1_OPEN_URL "\x1b[34;2m" "\x1b]8;;"
#define TTYN1_CLOSE_URL "\x1b\\"
#define TTYN1_RESET_URL "\x1b]8;;\x1b\\" "\x1b[39;22m"
#define TTYN1_DATA_URL "data:text/plain;charset=utf-8;base64,"

#define TTYN_HIGHLIGHT_BOLD "\x1b[1m"
#define TTYN_HIGHLIGHT_RESET "\x1b[0m"
#define TTYN_HIGHLIGHT_ERROR "\x1b[31;22m"
#define TTYN_HIGHLIGHT_WARNING "\x1b[38;5;228m"
#define TTYN_HIGHLIGHT_NOTICE "\x1b[34m"
#define TTYN_HIGHLIGHT_SYNOPSIS "\x1b[38;5;249m"

/**
	// Parameters needed to formulate a Status Frame.
*/
#define ttyn1_frame_parameters \
	stf_string_t channel, \
	stf_string_t type, \
	stf_string_t synopsis, \
	stf_string_t extension_data, \
	size_t extension_length

/**
	// Identify the exact size required to represent the TTYN.1 Status Frame.

	// [ Returns ]
	// Number of bytes required to hold the formatted frame.
*/
STF_API(size_t)
ttyn1_size_frame(stf_string_t channel, stf_string_t type, stf_string_t synopsis, size_t extension_length)
{
	size_t r = extension_length, dcount = 1;

	// Calculate decimal digits for extension size representation.
	#define _count_digits(N, D) \
		while (r >= D) \
		{ \
			r /= D; \
			dcount += N; \
		}
	_count_digits(1000000, 6)
	_count_digits(1000, 3)
	_count_digits(10, 1)
	#undef _count_digits

	return(
		1 + // "["
		strlen((const char *) type) +
		1 + // " "
		strlen((const char *) synopsis) +
		2 + // " ("
		strlen((const char *) channel) +
		sizeof(TTYN1_OPEN_URL) - 1 +
		sizeof(TTYN1_DATA_URL) - 1 +
		base64_encoded_size(extension_length) +
		sizeof(TTYN1_CLOSE_URL) - 1 +
		1 + // "+" signal
		(size_t) dcount,
		sizeof(TTYN1_RESET_URL) - 1 +
		sizeof(TTYN1_SIGNATURE) - 1 +
		3 // ")]\n"
	);
}

typedef uint64_t stf_count_t;
#define STF_COUNT_FMT "%" PRIu64
#define STF_METRICS_COUNT 11
#define TTYN_MAX_METRICS (20 * STF_METRICS_COUNT) + STF_METRICS_COUNT + 1

struct WorkMetrics {
	stf_count_t w_executed;
	stf_count_t w_granted;
	stf_count_t w_failed;
	stf_count_t w_prepared;
};

/**
	// Counts of primary work units.

	// [ Elements ]

	// /w_prepared/
		// Number of Work Units that will be performed.
	// /w_failed/
		// Number of Work Units that indicated failure.
	// /w_granted/
		// Number of Work Units that were already considered complete.
		// Tests skipped or cached results.
	// /w_executed/
		// Number of Work Units executed that did not indicate failure.
*/
typedef struct WorkMetrics stf_work_mt;
#define STF_WORK_CODE "%"
#define stf_work_zeros(S) (!S.w_executed + !S.w_granted + !S.w_failed + !S.w_prepared)
#define stf_work_format(FT) FT "+" FT "-" FT "/" FT
#define stf_work_arguments(S) \
	S.w_executed, \
	S.w_granted, \
	S.w_failed, \
	S.w_prepared

struct AdvisoryMetrics {
	stf_count_t m_notices;
	stf_count_t m_warnings;
	stf_count_t m_errors;
};

/**
	// Counts of errors, warnings, and other notifications that occurred.

	// [ Elements ]
	// /m_notices/
		// Number of messages that were not warnings or errors.
	// /m_warnings/
		// Number of warnings.
	// /m_errors/
		// Number of errors.
*/
typedef struct AdvisoryMetrics stf_advisory_mt;
#define STF_ADVISORY_CODE "@"
#define stf_advisory_zeros(S) (!S.m_notices + !S.m_warnings + !S.m_errors)
#define stf_advisory_format(FT) FT "!" FT "*" FT
#define stf_advisory_arguments(S) \
	S.m_notices, \
	S.m_warnings, \
	S.m_errors

struct ResourceMetrics {
	stf_count_t r_process;
	stf_count_t r_time;
	stf_count_t r_memory;
	stf_count_t r_divisions;
};

/**
	// Resource usage of the work.

	// [ Elements ]
	// /r_process/
		// Processor usage of the divisions.
	// /r_time/
		// The sum of the (real time) duration of all the divisions.
	// /r_memory/
		// Memory usage of the divisions.
	// /r_division/
		// Number of system processes that used the measured resources.
*/
typedef struct ResourceMetrics stf_resource_mt;
#define STF_RESOURCE_CODE "$"
#define stf_resource_zeros(S) (!S.r_process + !S.r_time + !S.r_memory + !S.r_divisions)
#define stf_resource_format(FT) FT ":" FT "#" FT "/" FT
#define stf_resource_arguments(S) \
	S.r_process, \
	S.r_time, \
	S.r_memory, \
	S.r_divisions

struct ProcedureStatus {
	stf_work_mt ps_work;
	stf_advisory_mt ps_message;
	stf_resource_mt ps_usage;
};

/**
	// Collection of common status measurements.

	// [ Elements ]
	// /ps_work/
		// Work Unit related counts.
	// /ps_message/
		// Counts of errors, warnings, and other notifications.
	// /ps_usage/
		// Memory, processor usage, duration, and work unit subdivisions.
*/
typedef struct ProcedureStatus stf_metrics_t;
#define stf_metrics_format(FT) \
	"%" STF_WORK_CODE stf_work_format(FT) \
	" " STF_ADVISORY_CODE stf_advisory_format(FT) \
	" " STF_RESOURCE_CODE stf_resource_format(FT)
#define stf_metrics_arguments(M) \
	stf_work_arguments(M->ps_work), \
	stf_advisory_arguments(M->ps_message), \
	stf_resource_arguments(M->ps_usage)

/**
	// Format the metrics into &buffer.
	// Generally presumes &length is sufficient, but will return negative
	// on &snprintf failures.

	// [ Parameters ]
	// /buffer/
		// Memory area to format the metrics string into.
	// /length/
		// Size of the buffer.
	// /psm/
		// The metrics to be formatted as a string.

	// [ Returns ]
	// Total number of bytes written into &buffer or a negative value
	// returned by &snprintf.
*/
STF_API(int)
stf_sequence_metrics(char *buffer, size_t length, stf_metrics_t *psm)
{
	int r, total = 0;
	char *p = buffer;

	// All zeros is empty string.
	*buffer = 0;

	if (stf_work_zeros(psm->ps_work) < sizeof(psm->ps_work) / sizeof(stf_count_t))
	{
		r = snprintf(p, length,
			"%" STF_WORK_CODE stf_work_format(STF_COUNT_FMT),
			stf_work_arguments(psm->ps_work)
		);
		if (r < 0)
			return(r);
	}
	else
		r = 0;

	total += r;
	p += r;
	length -= r;

	if (stf_advisory_zeros(psm->ps_message) < sizeof(psm->ps_message) / sizeof(stf_count_t))
	{
		r = snprintf(p, length,
			"%s" STF_ADVISORY_CODE stf_advisory_format(STF_COUNT_FMT),
			total > 0 ? " " : "",
			stf_advisory_arguments(psm->ps_message)
		);
		if (r < 0)
			return(r);
	}
	else
		r = 0;

	total += r;
	p += r;
	length -= r;

	if (stf_resource_zeros(psm->ps_usage) < sizeof(psm->ps_usage) / sizeof(stf_count_t))
	{
		r = snprintf(p, length,
			"%s" STF_RESOURCE_CODE stf_resource_format(STF_COUNT_FMT),
			total > 0 ? " " : "",
			stf_resource_arguments(psm->ps_usage)
		);
		if (r < 0)
			return(r);
	}
	else
		r = 0;

	return(total + r);
}

/**
	// Scan the &source for the field codes and fill &psm with
	// the corresponding values. Each section in &stf_metrics_t
	// is optional, but the order of the sets should be consistent
	// with the order in the string.

	// [ Parameters ]
	// /psm/
		// The metrics structure to fill.
	// /source/
		// The NUL-terminated string containing the field codes
		// with adjacent decimal values.

	// [ Returns ]
	// Number of sections (work, advisory, resource) found and scanned.
*/
STF_API(int)
stf_structure_metrics(stf_metrics_t *psm, const char *source)
{
	int r, t = 0;
	const char *p;

	p = strstr(source, "%");
	if (p != NULL)
	{
		r = sscanf(p+1,
			stf_work_format(STF_COUNT_FMT),
			stf_work_arguments(& psm->ps_work)
		);
		t += 1;

		p = strstr(p, "@");
	}
	else
	{
		psm->ps_work.w_executed = 0;
		psm->ps_work.w_failed = 0;
		psm->ps_work.w_granted = 0;
		psm->ps_work.w_prepared = 0;

		p = strstr(source, "@");
	}

	if (p != NULL)
	{
		r = sscanf(p+1,
			stf_advisory_format(STF_COUNT_FMT),
			stf_advisory_arguments(& psm->ps_message)
		);
		t += 1;

		p = strstr(p, "$");
	}
	else
	{
		psm->ps_message.m_notices = 0;
		psm->ps_message.m_warnings = 0;
		psm->ps_message.m_errors = 0;

		p = strstr(source, "$");
	}

	if (p != NULL)
	{
		r = sscanf(p+1,
			stf_resource_format(STF_COUNT_FMT),
			stf_resource_arguments(& psm->ps_usage)
		);

		t += 1;
	}
	else
	{
		psm->ps_usage.r_process = 0;
		psm->ps_usage.r_time = 0;
		psm->ps_usage.r_memory = 0;
		psm->ps_usage.r_divisions = 0;
	}

	return(t);
}

/**
	// Increase the indentation level of &txt by inserting &level count of
	// `'\t'` bytes after all `'\n'` bytes found in &txt.

	// Empty lines are not indented.

	// [ Parameters ]
	// /out/
		// Pointer to write the new allocation's address to.
	// /txt/
		// The text to copy that will have tabs inserted after newlines.
	// /length/
		// The length of the &txt; NUL characters are treated as regular
		// characters.
	// /estimate/
		// The presumed number of lines in &txt. If the exact number is known,
		// no reallocations should be necessary.
	// /level/
		// The number of tabs to insert.

	// [ Returns ]
	// Exact number of bytes written in &out.
	// The allocation size, of &out, may exceed this by some multiple of &level.
*/
STF_API(size_t)
stf_indent_text(uint8_t **out, stf_string_t txt, size_t length, uint16_t estimate, uint8_t level)
{
	size_t txtlen = length, count = 0;
	char *x = (char *) txt, *y;
	char *rs;
	size_t bufpos = 0, buflen = length + (estimate * level);

	// Estimate.
	rs = (char *) STF_MALLOC(buflen);
	if (rs == NULL)
	{
		*out = NULL;
		return(0);
	}

	if (txtlen > 0 && *x != '\n')
	{
		for (int i = 0; i < level; ++i)
			(rs + bufpos)[i] = '\t';
		bufpos += level;
	}

	while (y = (char *) memchr(x, (int) '\n', txtlen))
	{
		size_t d = ((intptr_t) y - (intptr_t) x);
		assert(txtlen >= d + 1);

		if (bufpos + d + level + 1 > buflen)
		{
			// There's enough for the entire content of &txt,
			// so this is only compensating for newlines beyond
			// the estimate.
			buflen += level * 8;
			rs = (char *) STF_REALLOC(rs, buflen);
			if (rs == NULL)
			{
				*out = NULL;
				return(0);
			}
		}

		assert((x + d)[0] == '\n');
		memcpy(rs + bufpos, x, d+1);
		bufpos += d + 1;

		// Advance search position beyond the identified newline.
		txtlen -= d + 1;
		x = y + 1;

		// Insert indentations; reallocation should guarantee available space.
		// Only indent lines with content.
		if (txtlen > 0 && *x != '\n')
		{
			for (int i = 0; i < level; ++i)
				(rs + bufpos)[i] = '\t';
			bufpos += level;
		}
	}

	// Remaining data in &txt without a trailing newline.
	memcpy(rs + bufpos, x, txtlen);

	*out = (uint8_t *) rs;
	return(bufpos + txtlen);
}

/**
	// Formatting to open an extended or channeled frame.
*/
#define ttyn1_format_open_frame(CHANNEL, TYPE, SYNOPSIS) \
	"[%s %s (" /* TYPE and SYNOPSIS. */ \
	"%s" /* CHANNEL */ \
	"%s", /* Open + URL */ \
	TYPE, \
	SYNOPSIS, \
	(CHANNEL ? (const char *) CHANNEL : ""), \
	TTYN1_OPEN_URL TTYN1_DATA_URL

/**
	// End of TTYN.1 frame formatting.
	// Used to finish a frame including a data extension.
*/
#define ttyn1_format_close_sized_frame(EXTLEN, LE) \
	"%s" /* Close */ \
	"+" /* Signal */ \
	"%lu" /* Extension Size */ \
	"%s" /* Reset + Signature */ \
	")]%s", \
	TTYN1_CLOSE_URL, \
	EXTLEN, \
	TTYN1_RESET_URL TTYN1_SIGNATURE, LE

/**
	// End of TTYN.1 frame formatting.
	// Used to finish a frame with a channel, but without a data extension.
*/
#define ttyn1_format_close_frame(EXTLEN, LE) \
	"%s)]%s", /* Signature */ \
	TTYN1_SIGNATURE, LE

/**
	// Signed TTYN.1 frame formatting.
	// Format an entire signed frame with no channel or data extensions.
*/
#define ttyn1_format_signed_frame(TYPE, SYNOPSIS, LE) \
	"[%s %s" /* TYPE and SYNOPSIS. */ \
	"%s" /* Signature */ \
	"]%s", \
	TYPE, SYNOPSIS, TTYN1_SIGNATURE, LE

/**
	// Unsigned TTYN.1 frame formatting.
	// Used to finish a frame with a channel, but without a data extension.
*/
#define ttyn1_format_unsigned_frame(TYPE, SYNOPSIS, LE) \
	"[%s %s]%s", /* TYPE, SYNOPSIS, Line End. */ \
	TYPE, SYNOPSIS, LE

/**
	// Common parameters used by the log and format message interfaces.
*/
#define ttyn1_message_parameters \
	stf_string_t channel, stf_string_t xid, struct iovec *ext, \
	stf_string_t type, stf_string_t context, \
	stf_string_t synopsis

/**
	// Common parameters used by the log and format transaction interfaces.
*/
#define ttyn1_transaction_parameters \
	stf_string_t channel, \
	stf_string_t xid, struct ProcedureStatus *psm, struct iovec *ext, \
	stf_string_t type, stf_string_t synopsis

#define _TTYN_OCTETS(SZ, DV) ((struct iovec) {(char *) DV, (size_t) SZ})

static inline struct iovec
_stf_sdprintf(uint8_t *buf, size_t length, const char *fmt, ...)
{
	int r;
	va_list vl;
	va_start(vl, fmt);
	r = vsnprintf((char *) buf, length, fmt, vl);
	va_end(vl);

	return(_TTYN_OCTETS(r, buf));
}

#define TTYN_INSERT_SECTION_FORMAT(SZ, KEY, FS, ...) \
	_stf_sdprintf(((uint8_t[SZ + sizeof(KEY) + sizeof(FS) + 1]){0,}), \
		SZ + sizeof(KEY ": " FS) + 1, \
		KEY ": " FS "\n" __VA_OPT__(,) __VA_ARGS__)
#define TTYN_INSERT_SIZED_OPTION(F, SZ, S) \
	_TTYN_OCTETS((S == NULL ? 0 : sizeof(F ": ")-1), (S == NULL ? (uint8_t *) "" : (uint8_t *) F ": ")), \
	_TTYN_OCTETS((S == NULL ? 0 : SZ), (S == NULL ? (uint8_t *) "" : S)), \
	_TTYN_OCTETS((S == NULL ? 0 : 1), (S == NULL ? (uint8_t *) "" : (uint8_t *) "\n"))

#define TTYN_INSERT(SZ, S) _TTYN_OCTETS(SZ, S)
#define TTYN_INSERT_SECTION(K, C) _TTYN_OCTETS(sizeof(K ": " C "\n")-1, K ": " C "\n")
#define TTYN_INSERT_OPTION(K, S) TTYN_INSERT_SIZED_OPTION(K, strlen((const char *) S), S)
#define TTYN_INSERT_CONSTANT(S) _TTYN_OCTETS(sizeof(S)-1, S)
#define TTYN_INSERT_STRING(S) _TTYN_OCTETS(strlen((const char *) S), S)
#define TTYN_INSERT_FORMAT(SZ, ...) _stf_sdprintf(((uint8_t[SZ]){0,}), SZ, __VA_ARGS__)
#define TTYN_INSERT_DECIMAL(S) TTYN_INSERT_FORMAT(22, "%" PRId64, (int64_t) S)
#define TTYN_INSERT_NEWLINE TTYN_INSERT(1, "\n")
#define TTYN_INSERT_ILINE_CONSTANT(S) TTYN_INSERT(sizeof(S) + 1, "\t" S "\n")

#define _TTYN_INSERT_CLOCK \
	TTYN_INSERT_SECTION_FORMAT(0, "@clock", "metric-seconds -9 2000-01-02")
#define _TTYN_INSERT_TIMESTAMP \
	TTYN_INSERT_SECTION_FORMAT(22, "@timestamp", "%" PRIu64, STF_CLOCK_TIMESTAMP())

#define TTYN_EXTENSION(...) (((struct iovec[]){__VA_ARGS__ __VA_OPT__(,) _TTYN_OCTETS(0, NULL)}))
#define TTYN_SYNOPSIS(...) (__VA_ARGS__)
#define _TTYN_FIRST(F, ...) F
#define _TTYN_TAIL(F, ...) __VA_ARGS__ __VA_OPT__(,)

static void
_ttyn1_copy_encoded(void *context, uint8_t *data, size_t length)
{
	struct iovec *buffer = (struct iovec *) context;

	// Zero length copies when buffer is full,
	// ttyn1_format_frame will check buffer status and report failure.
	if (length > buffer->iov_len)
		length = buffer->iov_len;

	memcpy(buffer->iov_base, data, length);
	buffer->iov_base = (void *) (((intptr_t) (buffer->iov_base)) + length);
	buffer->iov_len -= length;
}

STF_API(int)
_ttyn1_format_frame(uint8_t *buffer, size_t length,
	stf_string_t channel, stf_string_t type,
	stf_string_t synopsis, va_list sfp,
	struct iovec *context, struct iovec *application)
{
	int r = 0;
	size_t t = 0, ext_total = 0;
	uint8_t state[4] = {0,};
	struct iovec buf = {buffer, length};

	// TTYN_LOG macros modify the synopsis to include frame formatting.
	r = vsnprintf((char *)buf.iov_base, buf.iov_len, (const char *) synopsis, sfp);
	if (r < 0)
		return(r);
	t += r;
	buf.iov_len -= r;
	buf.iov_base = (void *) (((intptr_t) (buf.iov_base)) + r);

	// Base64 encode the extensions.
	ext_total += base64_transfer_encoded_v(state, _ttyn1_copy_encoded, (void *) &buf, context);
	ext_total += base64_transfer_encoded_v(state, _ttyn1_copy_encoded, (void *) &buf, application);

	// Finish the base64 encoded data when remainder is non-zero.
	if (state[0])
		t += base64_transfer_encoded_v(state, _ttyn1_copy_encoded, (void *) &buf,
			(struct iovec[2]) {(struct iovec){state, 0}, (struct iovec){NULL, 0}}
		);
	t += ext_total;

	// Final snprintf serves as error checking for the previous calls as well.
	r = snprintf((char *) buf.iov_base, buf.iov_len,
		"%s"  // Close URL
		"+"   // Signal
		"%lu" // Data extension size
		"%s"  // Reset + Signature
		")]\n",

		TTYN1_CLOSE_URL,
		base64_decoded_size(ext_total) + state[0],
		TTYN1_RESET_URL
		TTYN1_SIGNATURE
	);
	if (r < 0)
		return(r);

	return(r + t);
}

STF_API(int)
_ttyn1_format_message(uint8_t *buffer, size_t length, ttyn1_message_parameters, ...)
{
	int r;
	size_t synblength;
	va_list sfp;

	va_start(sfp, synopsis);

	r = _ttyn1_format_frame(buffer, length, channel, type, synopsis,
		sfp, TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP
		), ext
	);

	va_end(sfp);

	return(r);
}

#define _TTYN1_MESSAGE(TTYN_IF, C, XID, TYPE, HL, RST, CONTEXT, SYN, EXT, ...) \
	TTYN_IF(__VA_ARGS__, (stf_string_t) C, \
		(stf_string_t) XID, EXT, \
		(stf_string_t) TYPE, (stf_string_t) CONTEXT, \
		(stf_string_t) "[%s " \
		HL "%s" RST ": "\
		TTYN_HIGHLIGHT_SYNOPSIS _TTYN_FIRST SYN \
		TTYN_HIGHLIGHT_RESET " (%s%s", \
		TYPE, CONTEXT, _TTYN_TAIL SYN \
		(C ? (const char *) C : ""), \
		TTYN1_OPEN_URL TTYN1_DATA_URL \
	)

#define ttyn1_format_declaration(BUF, LEN, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_format_message, C, XID, "!?", "", "", "PROTOCOL", \
		TTYN_SYNOPSIS("%s tty-notation-1", STF_PROTOCOL), \
		TTYN_EXTENSION(_TTYN_INSERT_CLOCK __VA_OPT__(,) __VA_ARGS__), \
		BUF, LEN)
#define ttyn1_format_error(BUF, LEN, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_format_message, C, XID, "!#", TTYN_HIGHLIGHT_ERROR, TTYN_HIGHLIGHT_RESET, "ERROR", __VA_ARGS__, BUF, LEN)
#define ttyn1_format_warning(BUF, LEN, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_format_message, C, XID, "!#", TTYN_HIGHLIGHT_WARNING, TTYN_HIGHLIGHT_RESET, "WARNING", __VA_ARGS__, BUF, LEN)
#define ttyn1_format_notice(BUF, LEN, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_format_message, C, XID, "!#", TTYN_HIGHLIGHT_NOTICE, TTYN_HIGHLIGHT_RESET, "NOTICE", __VA_ARGS__, BUF, LEN)
#define ttyn1_format_trace(BUF, LEN, C, XID, CTX, ...) \
	_TTYN1_MESSAGE(_ttyn1_format_message, C, XID, "!~", "", "", CTX, __VA_ARGS__, BUF, LEN)

STF_API(int)
_ttyn1_format_transaction(uint8_t *buffer, size_t length, ttyn1_transaction_parameters, ...)
{
	int r;
	char msb[TTYN_MAX_METRICS];
	uint8_t *metrics;
	size_t mlength;
	va_list sfp;

	// @metrics
	if (psm != NULL)
	{
		mlength = stf_sequence_metrics(msb, sizeof(msb), psm);
		metrics = (uint8_t *) msb;
	}
	else
	{
		mlength = 0;
		metrics = (uint8_t *) NULL;
	}

	va_start(sfp, synopsis);
	r = _ttyn1_format_frame(buffer, length, channel, type, synopsis,
		sfp, TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP,
			TTYN_INSERT_SIZED_OPTION("@metrics", mlength, metrics)
		), ext
	);
	va_end(sfp);

	return(r);
}

#define _TTYN1_TRANSACTION(TTYN_IF, C, XID, M, TYPE, SYN, EXT, ...) \
	TTYN_IF(__VA_ARGS__, (stf_string_t) C, (stf_string_t) XID, M, EXT, \
		(stf_string_t) TYPE, \
		(stf_string_t) "[%s " _TTYN_FIRST SYN " (%s%s", \
		TYPE, \
		_TTYN_TAIL SYN \
		(C ? (const char *) C : ""), TTYN1_OPEN_URL TTYN1_DATA_URL \
	)

#define ttyn1_format_open_transaction(BUF, LEN, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_format_transaction, C, XID, M, "->", __VA_ARGS__, BUF, LEN)
#define ttyn1_format_update_transaction(BUF, LEN, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_format_transaction, C, XID, M, "--", __VA_ARGS__, BUF, LEN)
#define ttyn1_format_close_transaction(BUF, LEN, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_format_transaction, C, XID, M, "<-", __VA_ARGS__, BUF, LEN)

#define ttyn1_format_completed_transaction(BUF, LEN, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_format_transaction, C, XID, M, "<>", __VA_ARGS__, BUF, LEN)
#define ttyn1_format_failed_transaction(BUF, LEN, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_format_transaction, C, XID, M, "><", __VA_ARGS__, BUF, LEN)

static void
_ttyn1_write_encoded(void *context, uint8_t *data, size_t length)
{
	int fd = (intptr_t) context;
	write(fd, data, length);
}

/**
	// Log a TTYN.1 status frame.

	// [ Returns ]
	// Number of bytes written.
*/
STF_API(int)
_ttyn1_log_frame(int fd, stf_string_t channel, stf_string_t type, stf_string_t synopsis, va_list sfp,
	struct iovec *context, struct iovec *application)
{
	int r = 0;
	size_t t = 0, ext_total = 0;
	uint8_t state[4] = {0,};

	// TTYN_LOG macros modify the synopsis to include frame formatting.
	r = vdprintf(fd, (const char *) synopsis, sfp);
	if (r < 0)
		return(r);
	t += r;

	// Base64 encode the extensions.
	ext_total += base64_transfer_encoded_v(state, _ttyn1_write_encoded, (void *) fd, context);
	ext_total += base64_transfer_encoded_v(state, _ttyn1_write_encoded, (void *) fd, application);

	// Finish the base64 encoded data when remainder is non-zero.
	if (state[0])
		t += base64_transfer_encoded_v(state, _ttyn1_write_encoded, (void *) fd,
			(struct iovec[2]) {(struct iovec){state, 0}, (struct iovec){NULL, 0}}
		);
	t += ext_total;

	r = dprintf(fd,
		"%s"  // Close URL
		"+"   // Signal
		"%lu" // Data extension size
		"%s"  // Reset + Signature
		")]\n",

		TTYN1_CLOSE_URL,
		base64_decoded_size(ext_total) + state[0],
		TTYN1_RESET_URL
		TTYN1_SIGNATURE
	);
	if (r < 0)
		return(r);

	return(r + t);
}

STF_API(int)
_ttyn1_log_transaction(int fd, ttyn1_transaction_parameters, ...)
{
	int r;
	char msb[TTYN_MAX_METRICS];
	uint8_t *metrics;
	size_t mlength;
	va_list sfp;

	// @metrics
	if (psm != NULL)
	{
		mlength = stf_sequence_metrics(msb, sizeof(msb), psm);
		metrics = (uint8_t *) msb;
	}
	else
	{
		mlength = 0;
		metrics = (uint8_t *) NULL;
	}

	va_start(sfp, synopsis);
	r = _ttyn1_log_frame(fd, channel, type, synopsis, sfp,
		TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP,
			TTYN_INSERT_SIZED_OPTION("@metrics", mlength, metrics)
		),
		ext
	);
	va_end(sfp);

	return(r);
}

#define ttyn1_log_open_transaction(FD, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_log_transaction, C, XID, M, "->", __VA_ARGS__, FD)
#define ttyn1_log_update_transaction(FD, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_log_transaction, C, XID, M, "--", __VA_ARGS__, FD)
#define ttyn1_log_close_transaction(FD, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_log_transaction, C, XID, M, "<-", __VA_ARGS__, FD)

#define ttyn1_log_completed_transaction(FD, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_log_transaction, C, XID, M, "<>", __VA_ARGS__, FD)
#define ttyn1_log_failed_transaction(FD, C, XID, M, ...) \
	_TTYN1_TRANSACTION(_ttyn1_log_transaction, C, XID, M, "><", __VA_ARGS__, FD)

STF_API(int)
_ttyn1_log_message(int fd, ttyn1_message_parameters, ...)
{
	int r;
	size_t synblength;
	va_list sfp;

	va_start(sfp, synopsis);
	r = _ttyn1_log_frame(fd, channel, type, synopsis,
		sfp, TTYN_EXTENSION(
			TTYN_INSERT_OPTION("@transaction", xid),
			_TTYN_INSERT_TIMESTAMP
		), ext
	);
	va_end(sfp);

	return(r);
}

#define ttyn1_log_declaration(FD, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_log_message, C, XID, "!?", "", "", "PROTOCOL", \
		TTYN_SYNOPSIS("%s tty-notation-1", STF_PROTOCOL), \
		TTYN_EXTENSION(_TTYN_INSERT_CLOCK __VA_OPT__(,) __VA_ARGS__), \
		FD)
#define ttyn1_log_error(FD, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_log_message, C, XID, "!#", \
	TTYN_HIGHLIGHT_ERROR, TTYN_HIGHLIGHT_RESET, "ERROR", __VA_ARGS__, FD)
#define ttyn1_log_warning(FD, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_log_message, C, XID, "!#", \
	TTYN_HIGHLIGHT_WARNING, TTYN_HIGHLIGHT_RESET, "WARNING", __VA_ARGS__, FD)
#define ttyn1_log_notice(FD, C, XID, ...) \
	_TTYN1_MESSAGE(_ttyn1_log_message, C, XID, "!#", \
	TTYN_HIGHLIGHT_NOTICE, TTYN_HIGHLIGHT_RESET, "NOTICE", __VA_ARGS__, FD)
#define ttyn1_log_trace(FD, C, XID, CTX, ...) \
	_TTYN1_MESSAGE(_ttyn1_log_message, C, XID, "!~", "", "", CTX, __VA_ARGS__, FD)

#endif
