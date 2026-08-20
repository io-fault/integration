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

struct PathVector {
	size_t path_maximum_length;
	size_t path_count;
	const char *path_strings[0];
};
typedef struct PathVector path_vector_t;

path_vector_t *executable_paths(const char *pathenv);
int executable_scan(char *buffer, size_t length, path_vector_t *, const char *exename, int index);
const char *executable_first(const char *exename);

#define PW_NAME_FIELD(X) X->pw_name
#define PW_HOME_FIELD(X) X->pw_dir
#define PW_SHELL_FIELD(X) X->pw_shell
#define PW_TITLE_FIELD(X) X->pw_gecos
#define PW_CLASS_FIELD(X) X->pw_class

#if defined(__linux__) && !defined(UP_PWD_HAS_CLASS_FIELD)
	// Not available.
	#define PW_CLASS_FIELD(X) ""
#endif

#define USER_PROFILE_STRING_FIELDS(UP_FIELD) \
	UP_FIELD(name, PW_NAME_FIELD) \
	UP_FIELD(home, PW_HOME_FIELD) \
	UP_FIELD(shell, PW_SHELL_FIELD) \
	UP_FIELD(title, PW_TITLE_FIELD) \
	UP_FIELD(role, PW_CLASS_FIELD)

#define _UPF_COUNT(...) + 1
#define USER_PROFILE_STRING_COUNT (0 + USER_PROFILE_STRING_FIELDS(_UPF_COUNT))

struct UserProfile {
	uid_t u_identifier;

	#define UPC(X, PW) const char *u_##X ;
		USER_PROFILE_STRING_FIELDS(UPC)
	#undef UPC

	// String storage.
	char buffer[0];
};
typedef struct UserProfile user_profile_t;

user_profile_t *user_profile_convert_pwd(struct passwd *pwd);
user_profile_t *user_profile(uid_t uid);
const user_profile_t *current_user_profile(void);
void release_user_profile(void);
