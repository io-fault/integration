/**
	// Alternatively: -Wl,-sectcreate,__TEXT,__info_plist,Info.plist
*/

#ifndef MACOS_ACTIVATION_POLICY
	// NSApplicationActivationPolicyRegular
	#define MACOS_ACTIVATION_POLICY 1
#endif

// NSApplicationActivationPolicyProhibited
#define bundle_macos_background 0

// NSApplicationActivationPolicyAccessory
#define bundle_macos_accessory -1

#ifndef APPLE_INFO_PLIST_EXTENSION
	/**
		// Application local extensions.
	*/
	#define APPLE_INFO_PLIST_EXTENSION ""
#endif

#define PLSTRING(v) \
	"<string>" v "</string>"
#define PLSTR(k, v) \
	"<key>" #k "</key>" PLSTRING(v)
#define PLTRUE(k) "<key>" #k "</key><true/>"
#define PLFALSE(k) "<key>" #k "</key><false/>"

#ifndef MACOS_SYSTEM_MINIMUM
	#define MACOS_SYSTEM_MINIMUM "10.15"
#endif

#ifndef BUNDLE_PLATFORMS
	#define BUNDLE_PLATFORMS \
		PLSTRING("MacOSX")
#endif

#ifndef PLIST_VERSION
	#define PLIST_VERSION "1.0"
#endif

const char
__attribute__((section("__TEXT,__info_plist")))
embedded_info_plist_xml[] =
	"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
	"<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
	"\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
	"<plist version=\"" PLIST_VERSION "\"><dict>"
		#ifdef BUNDLE_INFO_VERSION
			PLSTR(CFBundleInfoDictionaryVersion, BUNDLE_INFO_VERSION)
		#endif

		#ifdef BUNDLE_PACKAGE_TYPE
			PLSTR(CFBundlePackageType, BUNDLE_PACKAGE_TYPE)
		#endif

		#ifdef BUNDLE_DEV_REGION
			PLSTR(CFBundleDevelopmentRegion, BUNDLE_REGION)
		#endif

		#ifdef BUNDLE_ID
			PLSTR(CFBundleIdentifier, BUNDLE_ID)
		#endif

		#ifdef BUNDLE_NAME
			PLSTR(CFBundleName, BUNDLE_NAME)
		#endif

		#ifdef BUNDLE_SHORT_VERSION
			PLSTR(CFBundleShortVersionString, BUNDLE_SHORT_VERSION)
		#endif

		#ifdef BUNDLE_VERSION
			PLSTR(CFBundleVersion, BUNDLE_VERSION)
		#endif

		#ifdef BUNDLE_EXECUTABLE
			PLSTR(CFBundleExecutable, BUNDLE_EXECUTABLE)
		#endif

		PLSTR(CFBundleSupportedPlatforms,
			"<array>"
				BUNDLE_PLATFORMS
			"</array>"
		)
		PLSTR(LSMinimumSystemVersion, MACOS_SYSTEM_MINIMUM)

		#ifdef PRINCIPAL_CLASS
			PLSTR(NSPrincipalClass, PRINCIPAL_CLASS)
		#endif

		#if MACOS_ACTIVATION_POLICY == bundle_macos_background
			PLTRUE(LSBackgroundOnly)
		#else
			PLFALSE(LSBackgroundOnly)
		#endif

		#if MACOS_ACTIVATION_POLICY == bundle_macos_accessory
			PLTRUE(LSUIElement)
		#else
			PLFALSE(LSUIElement)
		#endif

		#if !defined(DISABLE_HIGH_RESOLUTION_FLAG)
			PLTRUE(NSHighResolutionCapable)
		#endif

		APPLE_INFO_PLIST_EXTENSION
	"</dict></plist>"
;
