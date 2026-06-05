#define STF_PROTOCOL "http://fault.io/protocol/status/frames"

typedef const uint8_t * stf_string_t;

#define _STF_REFLECT(...) __VA_ARGS__
#define _STF_VOID(...)

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
