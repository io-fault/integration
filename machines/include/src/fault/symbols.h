/**
	// Define the necessary set of variables
	// for specifying imported, exported, and hidden symbols.
*/
#ifndef _FAULT_SYMBOLS_H_included_
#define _FAULT_SYMBOLS_H_included_
#define _fault_static static

#if defined(_MSC_VER)
	#ifdef CONFIG_DISABLE_SYMBOL
		#define _fault_symbol
		#define _fault_hide_symbol
		#define _fault_protect_symbol
		#define _fault_request_symbol
	#elif defined(_WIN16) && !defined(_WIN32)
		#define _fault_reveal_symbol __export
		#define _fault_hide_symbol
		#define _fault_protect_symbol
		#define _fault_request_symbol
	#else
		#define _fault_hide_symbol
		#define _fault_reveal_symbol __declspec(dllexport)
		/**
			// https://msdn.microsoft.com/en-us/library/a90k134d.aspx
			// https://docs.microsoft.com/en-us/cpp/build/exporting-from-a-dll-using-declspec-dllexport
		*/
		#define _fault_protect_symbol
		/**
			// https://msdn.microsoft.com/en-us/library/8fskxacy.aspx
			// https://docs.microsoft.com/en-us/cpp/build/importing-into-an-application-using-declspec-dllimport
		*/
		#define _fault_request_symbol __declspec(dllimport)
	#endif
#else
	#ifdef CONFIG_DISABLE_SYMBOL
		#define _fault_symbol
		#define _fault_hide_symbol
		#define _fault_protect_symbol
		#define _fault_request_symbol
	#elif __GNUC__ < 4
		#define _fault_symbol __attribute__ ((dllexport))
		#define _fault_request_symbol __attribute__ ((dllimport))
		#define _fault_protect_symbol
		#define _fault_hide_symbol
	#else
		#define _fault_reveal_symbol __attribute__ ((visibility ("default")))
		#define _fault_hide_symbol __attribute__ ((visibility ("hidden")))
		#define _fault_protect_symbol __attribute__ ((visibility ("protected")))
		#define _fault_request_symbol
	#endif
#endif

#define CONCEAL(...) _fault_hide_symbol __VA_ARGS__
#define PROTECT(...) _fault_protect_symbol __VA_ARGS__
#define STATIC(...) _fault_static __VA_ARGS__
#endif
