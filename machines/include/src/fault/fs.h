/**
	// High-level aggregate filesystem operations.
*/

#include <string.h>
#include <limits.h>
#include <sys/stat.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>

typedef enum {
	fs_mkdir_start_forwards = 1 << 0,
	fs_mkdir_dirty_failure = 1 << 1
} fs_mkdir_ctl;

/**
	// Allocate directories up to the final path entry.
*/
static int
fs_alloc(fs_mkdir_ctl ctlopt, const char *dirpath, const mode_t dmode)
{
	#ifndef SEPARATOR
		#define SEPARATOR '/'
	#endif

	#ifndef TERMINATOR
		#define TERMINATOR '\0'
	#endif

	int ncreated = 0;
	char buf[PATH_MAX];
	size_t len;
	char *p, *e;

	errno = 0;

	len = strlen(dirpath);
	if (len > sizeof(buf)-2)
	{
		errno = ENAMETOOLONG;
		return(-1);
	}

	bzero(buf, PATH_MAX);
	memcpy(buf, dirpath, len);
	buf[len] = SEPARATOR;
	buf[len+1] = TERMINATOR;

	/* Skip final path entry. */
	{
		e = buf + len;
		while (*e == SEPARATOR && e != buf)
			--e;
		while (*e != SEPARATOR && e != buf)
			--e;

		if (e == buf)
		{
			/* One path or only SEPARATOR. */
			return(0);
		}

		*e = SEPARATOR;
		*(e+1) = TERMINATOR;
	}

	if (ctlopt & fs_mkdir_start_forwards)
	{
		e = buf;
		if (*e != SEPARATOR)
			--e;
	}
	else
	{
		e = p = buf + len;
		++e; /* on the forced trailing slash */

		/* Backwards; skipped if dirpath equals "/" */
		while (p != buf)
		{
			if (*p == SEPARATOR)
			{
				*e = TERMINATOR;

				if (mkdir(buf, dmode) == 0)
				{
					*e = SEPARATOR;
					break;
				}
				else
				{
					if (errno == ENOTDIR)
					{
						/* Should never succeed. */
						return(-1);
					}

					errno = 0;
				}

				*e = SEPARATOR;
				e = p;
			}

			--p;
		}
	}

	/* Forwards */
	for (p = e + 1; *p != TERMINATOR; ++p)
	{
		if (*p == SEPARATOR)
		{
			*p = TERMINATOR;

			if (mkdir(buf, dmode) == 0)
				ncreated += 1;
			else
			{
				if (errno == EEXIST)
				{
					/* Directory already present. */
					;
				}
				else
				{
					/* Unacceptable failure. */
					goto failure;
				}
			}

			*p = SEPARATOR;
		}
	}

	return(0);

	/**
		//* WARNING: Relocate as separate function and remove control flag.
	*/
	failure:
	{
		/*
			// Directory in path could not be created.
		*/

		if (ctlopt & fs_mkdir_dirty_failure)
			return(-(ncreated + 1));

		if (ncreated > 0)
		{
			int err = errno; /* preserve original failure */
			errno = 0;

			e = p = buf + len;
			++e; /* on the forced trailing slash */

			/* Backwards */
			while (p != buf)
			{
				if (*p == SEPARATOR)
				{
					*e = TERMINATOR;

					if (unlink(buf) != 0)
					{
						errno = err;
						return(-(ncreated + 1));
					}
					else
					{
						if (--ncreated == 0)
							break;
					}

					e = p;
				}

				--p;
			}

			errno = err;
		}

		return(-(ncreated + 1));
	}

	#undef TERMINATOR
	#undef SEPARATOR
}

static int
fs_mkdir(const char *dirpath)
{
	int c = fs_alloc(0, dirpath, S_IRWXU|S_IRWXG|S_IRWXO);
	if (c < 0)
		return(c);

	if (mkdir(dirpath, S_IRWXU|S_IRWXG|S_IRWXO) != 0)
	{
		if (errno == EEXIST)
			errno = 0;
		else
			return(-c);
	}

	return(0);
}

static int
fs_init(fs_mkdir_ctl ctlopt, const char *path, const mode_t dmode, const mode_t fmode, const char *data)
{
	int fd;
	size_t len, i;

	if (fs_alloc(ctlopt, path, dmode) != 0)
		return(-1);

	fd = open(path, O_WRONLY);
	if (fd < 0)
		return(-2);

	len = strlen(data);
	i = 0;
	while (len > 0)
	{
		i = write(fd, data, len);
		if (i > 0)
		{
			len -= i;
			data += i;
		}
		else
			break;
	}

	close(fd);
	return(0);
}
