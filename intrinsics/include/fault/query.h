typedef double pmetric_size_t;
#define pmetric_size_maximum DBL_MAX
#define pmetric_size_format "f"

typedef double pmetric_time_t;
#define pmetric_time_maximum DBL_MAX
#define pmetric_time_format "f"

typedef uint_least32_t pmetric_count_t;
#define pmetric_count_format PRIoLEAST32

union ProcessMetricTypes {
	pmetric_count_t count;
	pmetric_size_t size;
	pmetric_time_t time;
};

const static struct {
	const char * const count;
	const char * const size;
	const char * const time;
} process_metric_formats = {
	pmetric_count_format,
	pmetric_size_format,
	pmetric_time_format
};

#define ProcessMetricsParameters(FIELD, COUNT, SIZE, TIME) \
	FIELD(COUNT, process_count) \
	FIELD(COUNT, thread_count) \
	FIELD(COUNT, suspended_count) \
	FIELD(COUNT, locked_count) \
	FIELD(COUNT, zombie_count) \
	\
	FIELD(TIME, maximum_elapsed_time) \
	FIELD(TIME, total_cumulative_time) \
	FIELD(TIME, total_user_time) \
	FIELD(TIME, total_system_time) \
	\
	FIELD(SIZE, average_memory) \
	FIELD(SIZE, average_maximum_memory) \
	FIELD(SIZE, maximum_memory)

struct ProcessMetrics {
	#define F(T, N) T N;
		ProcessMetricsParameters(F, pmetric_count_t, pmetric_size_t, pmetric_time_t)
	#undef F
};

typedef struct ProcessMetrics process_metrics_t;

/**
	// Accessor for generic switches and offset calculations.
*/
#define ProcessMetrics_Field(NAME) (((process_metrics_t *)0)->NAME)
int process_metrics_combine(process_metrics_t *, process_metrics_t **);

int process_usage_scan(process_metrics_t *, pid_t, size_t limit);
size_t process_executable_path(char *buf, size_t buflen, pid_t);
