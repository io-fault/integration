/**
	// Extract sources, regions, and counters from LLVM instrumented binaries and profile data files.
*/
#include <llvm/Config/llvm-config.h>

#include <llvm/ADT/DenseMap.h>

#if (LLVM_VERSION_MAJOR < 16)
	#include <llvm/ADT/Optional.h>
#endif

#include <llvm/ADT/SmallBitVector.h>
#include <llvm/ProfileData/Coverage/CoverageMapping.h>
#include <llvm/ProfileData/Coverage/CoverageMappingReader.h>

#if (LLVM_VERSION_MAJOR >= 17)
	#include <llvm/Support/VirtualFileSystem.h>
	#define CM_LOAD(object, data, arch) coverage::CoverageMapping::load( \
		ArrayRef(StringRef(object)), \
		StringRef(data), \
		*vfs::getRealFileSystem().get(), \
		ArrayRef(StringRef(arch)) \
	)
#elif (LLVM_VERSION_MAJOR >= 5)
	#define CM_LOAD(object, data, arch) coverage::CoverageMapping::load( \
		makeArrayRef(StringRef(object)), \
		StringRef(data), \
		StringRef(arch) \
	)
#else
	#define CM_LOAD coverage::CoverageMapping::load
#endif

#if (LLVM_VERSION_MAJOR >= 9)
	#define POSTv9(...) __VA_ARGS__
	#define CREATE_READER(BUF, ARCH, OBJBUFS) \
		coverage::BinaryCoverageReader::create(BUF->getMemBufferRef(), ARCH, OBJBUFS)
	#define ITER_CR_RECORDS(V, I) \
		for (const auto &_cov : I) \
		{ \
			for (auto V : (*_cov))

	#define ITER_CR_CLOSE() }
#else
	#define POSTv9(...)
	#define CREATE_READER(BUF, ARCH, OBJBUFS) \
		coverage::BinaryCoverageReader::create(BUF, ARCH)
	#define ITER_CR_RECORDS(V, I) \
		for (auto V : (*I))
	#define ITER_CR_CLOSE()
#endif

#include <llvm/ProfileData/InstrProfReader.h>
#include <llvm/Support/Debug.h>
#include <llvm/Support/Errc.h>
#include <llvm/Support/ErrorHandling.h>
#include <llvm/Support/ManagedStatic.h>
#include <llvm/Support/Path.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Support/TargetSelect.h>
#include <llvm/Object/ObjectFile.h>

#include <system_error>
#include <tuple>
#include <iostream>
#include <set>

#include <stddef.h>
#include <limits.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>

using namespace llvm;

static int kind_map[] = {
	1, -1, 0,
};

#define _llvm_error_object(X) (X).getError()
#define _llvm_error_string(X) (X).message().c_str()

#define CRE_GET_ERROR(X) ((X).takeError())
#define CMR_GET_ERROR(X) ((X).takeError())
#define ERR_STRING(X) toString(std::move(X)).c_str()
#define RECORD(X) (*X)

int
identify_architecture(char *buf, size_t len, char *image_path)
{
	Triple t;
	int r;
	auto bufref = MemoryBuffer::getFile(image_path);

	if (bufref.getError())
		return(-2);

	auto ob = object::ObjectFile::createObjectFile(bufref.get()->getMemBufferRef());
	t.setArch(ob->get()->getArch());

	r = snprintf(buf, len, "%.*s", t.getArchName().size(), t.getArchName().data());
	return(r);
}

/**
	// Identify the counts associated with the syntax areas.
*/
int
print_counters(FILE *fp, char *arch, char *object, char *datafile)
{
	auto mapping = CM_LOAD(object, datafile, arch);

	if (auto err = CRE_GET_ERROR(mapping))
	{
		fprintf(stderr, "ERROR: could not load coverage mapping counters.\n");
		fprintf(stderr, "LLVM: %s\n", ERR_STRING(err));
		return(1);
	}

	auto coverage = std::move(mapping.get());
	auto files = coverage.get()->getUniqueSourceFiles();

	for (auto &file : files)
	{
		auto data = coverage.get()->getCoverageForFile(file);
		if (data.empty())
			continue;

		// Split iteration, make sure there are non-zero counts before emitting path switch.
		auto seg = data.begin();
		for (; seg != data.end(); ++seg)
		{
			if (seg->HasCount && seg->Count > 0)
			{
				fprintf(fp, "@%.*s\n", (int) file.size(), file.data());
				break;
			}
		}

		for (; seg != data.end(); ++seg)
		{
			if (seg->HasCount && seg->Count > 0)
			{
				fprintf(fp, "%u %u %llu\n", seg->Line, seg->Col, seg->Count);
			}
		}
	}

	return(0);
}

/**
	// Identify the regions of the sources that may have counts.
*/
int
print_regions(FILE *fp, char *arch, char *object)
{
	int last = -1;
	auto CounterMappingBuff = MemoryBuffer::getFile(object);

	if (auto err = CounterMappingBuff.getError())
	{
		fprintf(stderr, "ERROR: could not load image file buffer.\n");
		fprintf(stderr, "LLVM: %s\n", _llvm_error_string(err));
		return(1);
	}

	POSTv9(SmallVector<std::unique_ptr<MemoryBuffer>, 4> bufs);

	auto CoverageReaderOrErr = CREATE_READER(CounterMappingBuff.get(), arch, bufs);
	if (!CoverageReaderOrErr)
	{
		fprintf(stderr, "ERROR: could not load counter mapping reader.\n");
		if (auto err = CRE_GET_ERROR(CoverageReaderOrErr))
			fprintf(stderr, "LLVM: %s\n", ERR_STRING(err));

		return(1);
	}

	ITER_CR_RECORDS(R, CoverageReaderOrErr.get())
	{
		if (CMR_GET_ERROR(R))
			continue;

		const auto &record = RECORD(R);
		auto fname = record.FunctionName;

		fprintf(fp, "@%.*s\n", (int) fname.size(), fname.data());
		last = -1;

		for (auto region : record.MappingRegions)
		{
			const char *kind;
			int ksz = 1;
			auto fi = region.FileID;

			if (fi != last)
			{
				auto fn = record.Filenames[fi];
				fprintf(fp, "%lu:%.*s\n", fi, (int) fn.size(), fn.data());
				last = fi;
			}

			switch (region.Kind)
			{
				case coverage::CounterMappingRegion::CodeRegion:
					kind = "+";
				break;

				case coverage::CounterMappingRegion::SkippedRegion:
					kind = "-";
				break;

				case coverage::CounterMappingRegion::ExpansionRegion:
					kind = "X";
					kind = record.Filenames[region.ExpandedFileID].data();
					ksz = record.Filenames[region.ExpandedFileID].size();
				break;

				case coverage::CounterMappingRegion::GapRegion:
					kind = ".";
				break;

				default:
					kind = "U";
				break;
			}

			fprintf(fp, "%lu %lu %lu %lu %.*s\n",
				(unsigned long) region.LineStart,
				(unsigned long) region.ColumnStart,
				(unsigned long) region.LineEnd,
				(unsigned long) region.ColumnEnd, ksz, kind);
		}
	}
	ITER_CR_CLOSE()

	return(0);
}

/**
	// Identify the set of source files associated with an image.
*/
int
print_sources(FILE *fp, char *arch, char *object)
{
	auto CounterMappingBuff = MemoryBuffer::getFile(object);

	if (auto err = CounterMappingBuff.getError())
	{
		fprintf(stderr, "ERROR: could not loader image file buffer.\n");
		fprintf(stderr, "LLVM: %s\n", _llvm_error_string(err));
		return(1);
	}

	POSTv9(SmallVector<std::unique_ptr<MemoryBuffer>, 4> bufs);

	auto CoverageReaderOrErr = CREATE_READER(CounterMappingBuff.get(), arch, bufs);
	if (!CoverageReaderOrErr)
	{
		if (auto err = CRE_GET_ERROR(CoverageReaderOrErr))
			fprintf(stderr, "%s\n", ERR_STRING(err));
		else
			fprintf(stderr, "unknown error\n");

		return(1);
	}

	std::set<std::string> paths;

	/*
		// The nested for loop will start a new section every time the fileid
		// changes so the reader can properly associate ranges.
	*/

	ITER_CR_RECORDS(R, CoverageReaderOrErr.get())
	{
		if (CMR_GET_ERROR(R))
			continue;

		const auto &record = RECORD(R);

		for (const auto path : record.Filenames)
		{
			/*
				// Usually one per function.
			*/
			paths.insert((std::string) path);
		}
	}
	ITER_CR_CLOSE()

	for (auto path : paths)
	{
		fprintf(fp, "%.*s\n", (int) path.length(), path.data());
	}

	return(0);
}

int
print_architectures(FILE *fp, char *image_path)
{
	Triple t;
	auto bufref = MemoryBuffer::getFile(image_path);

	if (auto err = bufref.getError())
	{
		fprintf(stderr, "%s\n", _llvm_error_string(err));
		return(1);
	}

	auto ob = object::ObjectFile::createObjectFile(bufref.get()->getMemBufferRef());
	t.setArch(ob->get()->getArch());
	fprintf(fp, "%.*s\n", t.getArchName().size(), t.getArchName().data());

	return(0);
}

int
main(int argc, char *argv[])
{
	char archbuf[128];
	char *arch;

	if (argc < 2 || strcmp(argv[1], "-h") == 0)
	{
		fprintf(stderr, "ipq architectures image-path\n");
		fprintf(stderr, "ipq regions image-path\n");
		fprintf(stderr, "ipq sources image-path\n");
		fprintf(stderr, "ipq counters image-path merged-profile-data\n");
		return(248);
	}

	if (strcmp(argv[1], "architectures") == 0)
	{
		if (argc != 3)
		{
			fprintf(stderr, "ERROR: architectures requires exactly one arguments.\n");
			return(1);
		}
		else
			return(print_architectures(stdout, argv[2]));
	}

	// Discover architecture from image if not defined via the environment.
	arch = getenv("IPQ_ARCHITECTURE");
	if (arch == NULL || strlen(arch) == 0)
	{
		identify_architecture(archbuf, sizeof(archbuf), argv[2]);
		arch = archbuf;
	}

	if (strcmp(argv[1], "regions") == 0)
	{
		if (argc != 3)
		{
			fprintf(stderr, "ERROR: regions requires two arguments.\n");
			return(1);
		}
		else
			return(print_regions(stdout, arch, argv[2]));
	}

	if (strcmp(argv[1], "sources") == 0)
	{
		if (argc != 3)
		{
			fprintf(stderr, "ERROR: sources requires one argument.\n");
			return(1);
		}
		else
			return(print_sources(stdout, arch, argv[2]));
	}

	if (strcmp(argv[1], "counters") == 0)
	{
		if (argc != 4)
		{
			fprintf(stderr, "ERROR: counters requires two arguments.\n");
			return(1);
		}
		else
			return(print_counters(stdout, arch, argv[2], argv[3]));
	}

	fprintf(stderr, "unrecognized command: '%s'\n", argv[1]);
	return(2);
}
