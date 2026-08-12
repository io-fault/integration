/**
	// Functions and types for getting high-level user and process status information
	// from the system.
*/
#ifdef __linux__
	#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <inttypes.h>
#include <signal.h>
#include <fcntl.h>
#include <time.h>
#include <sys/time.h>
#include <sys/param.h>
#include <sys/user.h>
#include <sys/types.h>

#include <fault/query.h>

/**
	// Type used for representing data measurements.

	// The use of a double here is potentially necessary to handle
	// larger groups where maximum memory sums can become very large.
	// While physical constraints may make 64-bits suitable and exact, prefer
	// floating point in order to handle virtual cases as well.
*/
typedef double pmetric_size_t;

/**
	// Type used for representing time measurements; primarily processor usage times.

	// The use of a double here is necessary as the aggregate usage times
	// can become very large, very quickly, if precision is not to be discarded.
*/
typedef double pmetric_time_t;

#define pm_convert_timespec(V) \
	(((pmetric_time_t) ((V).tv_sec)) + (((pmetric_time_t) (V).tv_nsec) / 1000000000))

#define pm_convert_timeval(V) \
	(((pmetric_time_t) ((V).tv_sec)) + (((pmetric_time_t) (V).tv_usec) / 1000000))

#define pm_convert_machtime_context(x) \
	mach_timebase_info_data_t x; mach_timebase_info(&x)

#define pm_convert_machtime(mti, x) \
	(((((pmetric_time_t) x) * mti.numer) / mti.denom) / 1000000000)

/**
	// Type used for representing relatively small counts.
*/
typedef uint_least32_t pmetric_count_t;

/**
	// Types used by &process_metrics_t.
*/
typedef union ProcessMetricTypes pmetric_types_u;

/**
	// Report structure used to communicate process resource usage.

	// [ Elements ]
	// /process_count/
		// Total number of processes measured.
	// /thread_count/
		// Total number of threads running in the processes.
	// /suspended_count/
		// Number of processes reported to have been paused that may require
		// explicit signaling in order to continue.
	// /locked_count/
		// Number of processes reported to be awaiting a lock.
	// /zombie_count/
		// Number of processes reported to be in a zombie state.

	// /maximum_elapsed_time/
		// The current duration of the earliest running process.
	// /total_cumulative_time/
		// The sum of the runtimes of the processes.
	// /total_user_time/
		// The sum of the reported CPU user time for the divisions.
	// /total_system_time/
		// The sum of the reported CPU system time for the divisions.

	// /average_memory/
		// The average memory usage of the scanned processes.
	// /average_maximum_memory/
		// The average maximum memory usage of the scanned processes.
		// Zero if not available.
	// /maximum_memory/
		// The highest maximum memory usage of the scanned processes.
*/
typedef struct ProcessMetrics process_metrics_t;

/**
	// Aggregate the given source metrics, &src, into &av;

	// [ Parameters ]
	// /av/
		// The memory to write the aggregate into.
	// /src/
		// NULL-terminated array of process_metrics_t pointers.
		// `(process_metric_t *[]){&A, &B, NULL}`.
	// [ Returns ]
	// The number of records processed from &src.
*/
int
process_metrics_combine(process_metrics_t *av, process_metrics_t **src)
{
	pmetric_time_t duration = av->maximum_elapsed_time;
	int i;

	// Expand average for sum.
	av->average_memory *= av->process_count;
	av->average_maximum_memory *= av->process_count;

	for (i = 0; src[i] != NULL; ++i)
	{
		process_metrics_t *c = src[i];
		pmetric_count_t units = c->process_count == 0 ? 1 : c->process_count;

		av->process_count += c->process_count;
		av->thread_count += c->thread_count;
		av->zombie_count += c->zombie_count;
		av->suspended_count += c->suspended_count;
		av->locked_count += c->locked_count;

		av->total_cumulative_time += c->total_cumulative_time;
		av->total_user_time += c->total_user_time;
		av->total_system_time += c->total_system_time;

		if (av->maximum_elapsed_time < c->maximum_elapsed_time)
			av->maximum_elapsed_time = c->maximum_elapsed_time;
		if (av->maximum_memory < c->maximum_memory)
			av->maximum_memory = c->maximum_memory;

		av->average_memory += c->average_memory * c->process_count;
		av->average_maximum_memory += c->average_maximum_memory * c->process_count;
	}

	// Redistribute the temporarily held total.
	av->average_memory /= av->process_count;
	av->average_maximum_memory /= av->process_count;

	return(i);
}

#ifndef SQ_PROCESS_USAGE_INTERFACE
	/**
		// Signal for (process usage) interface selection override.
	*/
	#define SQ_PROCESS_USAGE_INTERFACE "void"

	#if defined(__FreeBSD__) || defined(__NetBSD__)
		#define SQ_PROCESS_SYSCTL_INTERFACES 1
		#define SQ_PROCESS_USAGE_INTERFACE "sysctl-KERN_PROC"
	#elif defined(__OpenBSD__) || defined(__DragonFly__)
		#define SQ_PROCESS_SYSCTL_INTERFACES 1
		#define SQ_PROCESS_USAGE_INTERFACE "sysctl-KERN_PROC"
	#elif defined(__MACH__)
		#define SQ_MACOS_LIBPROC_INTERFACES 2
		#define SQ_PROCESS_USAGE_INTERFACE "macos-libproc"
	#elif defined(__linux__)
		#define SQ_LINUX_PROCFS_INTERFACES 3
		#define SQ_PROCESS_USAGE_INTERFACE "linux-procfs"
	#else
		#define SQ_VOID_USAGE_INTERFACES -1
	#endif
#endif

#if SQ_PROCESS_SYSCTL_INTERFACES
	#include <sys/sysctl.h>
	#define BSD_MAXRSS_FACTOR 1024

	size_t
	process_executable_path(char *path, size_t path_length, pid_t pid)
	{
		int r;
		int mib[] = {
			CTL_KERN, KERN_PROC, KERN_PROC_PATHNAME, pid
		};

		r = sysctl(mib, 4, path, &path_length, NULL, 0);
		path[path_length] = '\0';
		return(r);
	}

	static void
	measure_process_usage(process_metrics_t *report, struct kinfo_proc *p, size_t count)
	{
		long page_size = sysconf(_SC_PAGESIZE);
		struct timeval now_tv = {0,};
		pmetric_time_t now, time = 0, rtime = 0, ctime = 0, utime = 0, stime = 0;
		pmetric_size_t memory = 0, mmax = 0, mmax_sum = 0;
		pmetric_count_t tcount = 0, scount = 0, zcount = 0, lcount = 0;

		gettimeofday(&now_tv, NULL);
		now = pm_convert_timeval(now_tv);
		for (size_t i = 0; i < count; ++i)
		{
			struct kinfo_proc *c = &p[i];
			struct rusage *u;
			pmetric_size_t r_memory;

			time = now - pm_convert_timeval(c->ki_start);
			ctime += time;
			ctime += pm_convert_timeval(c->ki_childtime);
			if (rtime < time)
				rtime = time;

			r_memory = c->ki_rssize * page_size;
			r_memory += c->ki_ssize * page_size;

			memory += r_memory;

			u = &c->ki_rusage;
			{
				utime += pm_convert_timeval(u->ru_utime);
				stime += pm_convert_timeval(u->ru_stime);
				if (u->ru_maxrss > mmax)
					mmax = u->ru_maxrss;
				mmax_sum += u->ru_maxrss;
			}

			u = &c->ki_rusage_ch;
			{
				utime += pm_convert_timeval(u->ru_utime);
				stime += pm_convert_timeval(u->ru_stime);

				/* Not currently filled by FreeBSD. */
				if (u->ru_maxrss > mmax)
					mmax = u->ru_maxrss;
			}

			tcount += c->ki_numthreads;
			switch (c->ki_stat)
			{
				case SSTOP:
					scount += 1;
				break;

				case SZOMB:
					zcount += 1;
				break;

				case SLOCK:
					lcount += 1;
				break;
			}
		}
		#undef timev

		report->total_cumulative_time += ctime;
		report->total_user_time += utime;
		report->total_system_time += stime;
		if (report->maximum_elapsed_time < rtime)
			report->maximum_elapsed_time = rtime;

		report->suspended_count += scount;
		report->locked_count += lcount;
		report->zombie_count += zcount;

		report->average_memory *= report->process_count;
		report->average_memory += memory;
		report->average_maximum_memory *= report->process_count;
		report->average_maximum_memory += mmax_sum * BSD_MAXRSS_FACTOR;

		if (report->maximum_memory < mmax * BSD_MAXRSS_FACTOR)
			report->maximum_memory = mmax * BSD_MAXRSS_FACTOR;

		report->process_count += count;
		report->thread_count += tcount;
		report->average_memory /= report->process_count;
		report->average_maximum_memory /= report->process_count;
	}

	int
	process_usage_scan(process_metrics_t *report, pid_t id, size_t limit)
	{
		size_t count = 0;
		size_t p_length = 0;
		size_t l_length = limit * sizeof(struct kinfo_proc);
		struct kinfo_proc *p;
		int pgroup_name[4] = {CTL_KERN, KERN_PROC, KERN_PROC_PGRP, -id};
		int process_name[4] = {CTL_KERN, KERN_PROC, KERN_PROC_PID, id};
		int *name = id < 0 ? pgroup_name : process_name;

		if (limit > 16)
		{
			// Larger limit; query for size.
			if (sysctl(name, 4, NULL, &p_length, NULL, 0) == -1)
				return(-2);

			// No data.
			if (p_length == 0)
				return(0);

			// Restrict size to limit.
			if (p_length > l_length)
				p_length = l_length;
		}
		else
		{
			// Small limit; just allocate it.
			p_length = l_length;
		}

		p = malloc(p_length);
		if (p == NULL)
			return(-1);

		if (sysctl(name, 4, p, &p_length, NULL, 0) == -1)
		{
			free(p);
			return(-3);
		}

		count = p_length / sizeof(struct kinfo_proc);
		if (count > limit)
			count = limit;

		measure_process_usage(report, p, count);
		free(p);
		return(0);
	}
#elif defined(SQ_MACOS_LIBPROC_INTERFACES)
	#include <libproc.h>
	#include <sys/proc_info.h>
	#include <mach/mach_time.h>

	#define MACOS_MAXRSS_FACTOR 1024

	static int
	measure_process_usage(process_metrics_t *report, pid_t *pv, size_t count)
	{
		pmetric_count_t tcount = 0, scount = 0, zcount = 0;
		pmetric_time_t now, time, rtime = 0, ctime = 0, stime = 0, utime = 0;
		pmetric_size_t memory = 0, mmax = 0, mmax_sum = 0;

		uint64_t mtime;
		pm_convert_machtime_context(mti);

		mtime = mach_absolute_time();
		for (int i = 0; i < count; ++i)
		{
			int info_size = 0;
			struct proc_bsdshortinfo bi;
			struct proc_taskinfo ti;
			rusage_info_current ru = {0,};
			uint_least64_t d;

			if (proc_pid_rusage(pv[i], RUSAGE_INFO_CURRENT, (void *) &ru) < 0)
				continue;

			time = pm_convert_machtime(mti, mtime - ru.ri_proc_start_abstime);
			if (rtime < time)
				rtime = time;

			ctime += time;
			ctime += pm_convert_machtime(mti, ru.ri_child_elapsed_abstime);
			utime += pm_convert_machtime(mti, ru.ri_user_time + ru.ri_child_user_time);
			stime += pm_convert_machtime(mti, ru.ri_system_time + ru.ri_child_system_time);

			memory += ru.ri_phys_footprint;
			mmax_sum += ru.ri_lifetime_max_phys_footprint;

			if (ru.ri_lifetime_max_phys_footprint > mmax)
				mmax = ru.ri_lifetime_max_phys_footprint;

			info_size = proc_pidinfo(pv[i], PROC_PIDT_SHORTBSDINFO, 0, &bi, sizeof(bi));
			if (info_size < 0)
				bi.pbsi_status = 0;

			switch (bi.pbsi_status)
			{
				case SSTOP:
					scount += 1;
				break;

				case SZOMB:
					zcount += 1;
				break;
			}

			info_size = proc_pidinfo(pv[i], PROC_PIDTASKINFO, 0, &ti, PROC_PIDTASKINFO_SIZE);
			if (info_size == PROC_PIDTASKINFO_SIZE)
			{
				tcount += ti.pti_threadnum;
			}
		}

		report->total_cumulative_time += ctime;
		report->total_user_time += utime;
		report->total_system_time += stime;
		if (report->maximum_elapsed_time < rtime)
			report->maximum_elapsed_time = rtime;

		report->suspended_count += scount;
		report->zombie_count += zcount;
		report->locked_count += 0;

		report->average_memory *= report->process_count;
		report->average_memory += memory;

		report->average_maximum_memory *= report->process_count;
		report->average_maximum_memory += mmax_sum * MACOS_MAXRSS_FACTOR;

		report->maximum_memory = mmax * MACOS_MAXRSS_FACTOR;

		report->process_count += count;
		report->thread_count += tcount;
		report->average_memory /= report->process_count;
		report->average_maximum_memory /= report->process_count;

		return(0);
	}

	int
	process_usage_scan(process_metrics_t *report, pid_t id, size_t limit)
	{
		const size_t ds = sizeof(pid_t) * limit;

		#if 0
			int current;
			current = 0;
			do
			{
				const size_t rs = sizeof(pid_t) * n;

				n += proc_listchildpids(cpids[current], &(cpids[n]), ds - rs);
				if (n >= limit)
					break;

				++current;
			} while (current < n);
		#endif

		if (id >= 0)
			measure_process_usage(report, &id, 1);
		else
		{
			int n;
			pid_t *cpids = alloca(ds);
			n = proc_listpgrppids(-id, cpids, ds);
			measure_process_usage(report, cpids, n);
		}

		return(0);
	}

	size_t
	process_executable_path(char *buffer, size_t length, pid_t process)
	{
		return((size_t) proc_pidpath(process, buffer, length));
	}
#elif defined(SQ_LINUX_PROCFS_INTERFACES)
	#include <assert.h>
	#include <string.h>
	#include <sys/stat.h>

	size_t
	process_executable_path(char *buffer, size_t buflen, pid_t pid)
	{
		ssize_t bytes_read;
		const char *path;
		char procpath[64];
		int fd;

		snprintf(procpath, sizeof(procpath), "/proc/%lu/exe", (unsigned long) pid);
		bytes_read = readlink(procpath, buffer, buflen-1);
		buffer[bytes_read >= 0 ? bytes_read : 0] = '\0';

		return(bytes_read);
	}

	static size_t
	read_proc_file(char *buf, size_t bufsize, pid_t process, const char *filename)
	{
		ssize_t bytes_read;
		const char *path;
		char procpath[256];
		int fd;

		snprintf(procpath, sizeof(procpath), "/proc/%lu/%s", (unsigned long) process, filename);
		fd = open(procpath, O_RDONLY|O_CLOEXEC);
		if (fd < 0)
			return(-1);

		bytes_read = read(fd, buf, bufsize);
		buf[bytes_read-1] = 0;
		close(fd);

		return(bytes_read);
	}

	static int
	control_group_open_path(const char *sysfs, const char *cgpath)
	{
		int fd;

		if (cgpath[0] != '/')
		{
			int rfd = open(sysfs, O_PATH|O_DIRECTORY|O_CLOEXEC);
			if (rfd < 0)
				return(-1);

			fd = openat(rfd, cgpath, O_PATH|O_DIRECTORY|O_CLOEXEC);
			close(rfd);
		}
		else
			fd = open(cgpath, O_PATH|O_DIRECTORY|O_CLOEXEC);

		return(fd);
	}

	static int
	control_group_open_process(pid_t process)
	{
		ssize_t bytes_read;
		char buf[4096];
		const char *path;
		char procpath[256];

		if (read_proc_file(buf, sizeof(buf), process, "cgroup") < 0)
			return(-1);

		// Find the start of the path and advance one more. (openat)
		path = buf;
		while (*path != '/')
			++path;
		++path;

		return(control_group_open_path("/sys/fs/cgroup", path));
	}

	static uint64_t
	control_group_read_integer_record(int cgroup, const char *name)
	{
		unsigned long long r;
		char buf[64];
		ssize_t bytes_read;
		int fd;

		fd = openat(cgroup, name, O_RDONLY);
		if (fd < 0)
			return(0);
		else
		{
			bytes_read = read(fd, buf, sizeof(buf));
			buf[bytes_read] = '\0';
			r = strtoull((const char *) buf, NULL, 10);
		}
		close(fd);

		return((uint64_t) r);
	}

	static void
	control_group_read_cpu_times(process_metrics_t *report, int cgroup)
	{
		unsigned long long r;
		char buf[256];
		char *end = NULL;
		char *user_cursor, *system_cursor;
		ssize_t bytes_read;
		int fd;

		fd = openat(cgroup, "cpu.stat", O_RDONLY);
		if (fd < 0)
			return;

		bytes_read = read(fd, buf, sizeof(buf));
		buf[bytes_read] = '\0';
		close(fd);

		#define sseek(N) strstr(buf, N) + sizeof(N)
		user_cursor = sseek("user_usec");
		system_cursor = sseek("system_usec");

		report->total_user_time = strtoull((const char *) user_cursor, &end, 10);
		report->total_user_time /= 1000000;

		report->total_system_time = strtoull((const char *) system_cursor, &end, 10);
		report->total_system_time /= 1000000;
		#undef sseek
	}

	static int
	control_group_read_metrics(process_metrics_t *report, pid_t process)
	{
		int cg = control_group_open_process(process);
		struct stat statbuf = {0,};
		struct timespec now_ts = {0,};
		pmetric_time_t now;

		clock_gettime(CLOCK_REALTIME, &now_ts);
		now = pm_convert_timespec(now_ts);

		#define cgri(N) control_group_read_integer_record(cg, N)
		report->process_count = cgri("pids.current");
		if (report->process_count > 0)
		{
			// Presume zero memory if zero process count. (likely missing files)
			report->average_memory = cgri("memory.current") / report->process_count;
		}
		report->maximum_memory = cgri("memory.peak");
		#undef cgri

		control_group_read_cpu_times(report, cg);

		if (fstatat(cg, "cgroup.controllers", &statbuf, 0) < 0)
			;
		else
		{
			struct timespec *t;

			// Earliest time.
			if (statbuf.st_mtim.tv_sec < statbuf.st_ctim.tv_sec)
				t = &statbuf.st_mtim;
			else
			{
				if (statbuf.st_mtim.tv_sec == statbuf.st_ctim.tv_sec)
				{
					if (statbuf.st_mtim.tv_nsec < statbuf.st_ctim.tv_nsec)
						t = &statbuf.st_mtim;
					else
						t = &statbuf.st_ctim;
				}
				else
					t = &statbuf.st_ctim;
			}

			now -= t->tv_sec;
			now -= t->tv_nsec / 1000000000;
			if (report->maximum_elapsed_time < now)
				report->maximum_elapsed_time = now;
		}

		close(cg);
	}

	struct ProcessMetricsLinuxRecord {
		char state;
		unsigned long utime;
		unsigned long stime;
		signed long cutime;
		signed long cstime;
		signed long num_threads;
		unsigned long long starttime; // Time since boot.
		signed long rss;
		unsigned long vmhwm; // Max resident, from `/proc/#/status`.
	};
	typedef struct ProcessMetricsLinuxRecord pm_linux_record_t;

	static int
	measure_process_usage(process_metrics_t *report, pm_linux_record_t *lrs, size_t count)
	{
		pmetric_count_t tcount = 0, scount = 0, zcount = 0;
		pmetric_time_t now, rtime = 0, ctime = 0, stime = 0, utime = 0;
		pmetric_size_t memory = 0, mmax = 0, mmax_sum = 0;
		struct timespec now_ts = {0,};
		long tps = sysconf(_SC_CLK_TCK);
		long page_size = sysconf(_SC_PAGESIZE);

		clock_gettime(CLOCK_BOOTTIME, &now_ts);

		for (int i = 0; i < count; ++i)
		{
			pm_linux_record_t *r = &lrs[i];
			pmetric_time_t duration;

			duration = now_ts.tv_sec;
			duration += (pmetric_time_t) now_ts.tv_nsec / 1000000000;
			duration -= ((pmetric_time_t) r->starttime / tps);
			if (rtime < duration)
				rtime = duration;

			memory += r->rss * page_size;
			mmax_sum += r->vmhwm;
			if (mmax < r->vmhwm)
				mmax = r->vmhwm;

			switch (r->state)
			{
				case 'Z':
					zcount += 1;
				break;

				case 'T':
					scount += 1;
				break;
			}

			tcount += r->num_threads;
			stime += (pmetric_time_t) r->stime / tps;
			if (r->cstime >= 0)
				stime += (pmetric_time_t) r->stime / tps;

			utime += (pmetric_time_t) r->utime / tps;
			if (r->cutime >= 0)
				utime += (pmetric_time_t) r->cutime / tps;
		}

		report->total_cumulative_time += ctime;
		report->total_user_time += utime;
		report->total_system_time += stime;
		if (report->maximum_elapsed_time < rtime)
			report->maximum_elapsed_time = rtime;

		report->suspended_count += scount;
		report->zombie_count += zcount;
		report->locked_count += 0;

		report->average_memory *= report->process_count;
		report->average_memory += memory;
		report->average_maximum_memory *= report->process_count;
		report->average_maximum_memory += mmax_sum;

		if (report->maximum_memory < mmax)
			report->maximum_memory = mmax;

		report->process_count += count;
		report->thread_count += tcount;
		report->average_memory /= report->process_count;
		report->average_maximum_memory /= report->process_count;

		return(0);
	}

	int
	process_usage_scan(process_metrics_t *report, pid_t id, size_t limit)
	{
		pm_linux_record_t lps = {0,};
		char buf[2048];
		char *hwm = NULL;

		if (id < 0)
		{
			// Read cgroup.
			return(control_group_read_metrics(report, -id));
		}

		if (read_proc_file(buf, sizeof(buf)-1, id, "stat") < 0)
			return(-1);

		sscanf(buf,
			"%*d %*s "
			"%c" // state
			" %*d %*d %*d %*d %*d"
			" %*u %*lu %*lu %*lu %*lu "
			"%lu " // user time
			"%lu " // system time
			"%ld " // wfc user time
			"%ld" // wfc system time
			" %*ld %*ld "
			"%ld" // num_threads
			" %*ld "
			"%llu" // starttime
			" %*lu "
			"%ld" // rss
			"",
			&lps.state,
			&lps.utime, &lps.stime,
			&lps.cutime, &lps.cstime,
			&lps.num_threads,
			&lps.starttime,
			&lps.rss
		);

		lps.vmhwm = 0;
		if (read_proc_file(buf, sizeof(buf) / 2, id, "status") >= 0)
		{
			hwm = strcasestr(buf, "\nVmHWM:");
			if (hwm != NULL)
			{
				hwm += sizeof("\nVmHWM:");
				lps.vmhwm = strtoull((const char *) hwm, NULL, 10) * 1024;
			}
		}

		measure_process_usage(report, &lps, 1);
		return(0);
	}
#else
	/**
		// Retrieve the executable path of the identified process.

		// [ Parameters ]
		// /buffer/
			// The space to write the path into.
		// /length/
			// The available number of bytes in &buffer.
		// /process/
			// The identifier of the process to lookup.

		// [ Returns ]
		// Number of bytes written into &buffer excluding the NUL terminator.

		// [ Linux ]
		// Read the link at `"proc/%lu/exe"` into the given &buffer
		// limited by &buflen. A maximum of &buflen minus `1` characters
		// will be read in order to keep room for termination.
	*/
	size_t
	process_executable_path(char *buffer, size_t length, pid_t process)
	{
		return(0);
	}

	/**
		// Aggregate resource usage information about a process or collection of
		// processes selected using &id.

		// [ Parameters ]
		// /report/
			// The aggregate metrics' destination.
		// /id/
			// The process identifier or group identifier to use
			// find usage information about. When negative, scan the process'
			// associated process group (pgid) or control group (linux).
		// /limit/
			// Maximum number of usage records to lookup and aggregate.
			// When looking up a sole process, always set this to `1` in
			// order to avoid tree scans.

		// [ Returns ]
		// The number failed reads that occurred during aggregation. Essentially,
		// a minimal indication of whether or not information may or may not be
		// missing from the aggregate. For fixed process collections, this is not
		// likely to occur, but for active ones, aggregation is racing with
		// process exits and will may not have an accurate snapshot.

		// [ Exceptions ]
		// Errors that occur during the collection of measurements are tallied, but
		// ignored; the information presented in &report is whatever the system was
		// able to provide at the time.

		// [ Linux ]
		// Take process usage status readings from the proc filesystem, `/proc`,
		// and aggregate them into &report. If the &id is negative, read and convert
		// the aggregated data from the process' control group.

		// Currently, process scans do not include the tree, but will in the future.
	*/
	int
	process_usage_scan(process_metrics_t *report, pid_t id, size_t limit)
	{
		return(0);
	}
#endif
