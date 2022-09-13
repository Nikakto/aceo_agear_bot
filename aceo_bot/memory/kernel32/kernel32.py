import ctypes

from . import types


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

get_enum_process_modules = ctypes.windll.psapi.EnumProcessModules
get_enum_process_modules.restype = ctypes.wintypes.BOOL
get_enum_process_modules.argtypes = (ctypes.wintypes.LPCSTR,)

get_last_error = kernel32.GetLastError

get_module_handle = kernel32.GetModuleHandleA
get_module_handle.restype = ctypes.wintypes.HMODULE
get_module_handle.argtypes = (ctypes.wintypes.LPCSTR,)


"""https://docs.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getmoduleinformation"""
get_module_base_address = ctypes.windll.psapi.GetModuleInformation
get_module_base_address.restype = ctypes.wintypes.HANDLE
get_module_base_address.argtypes = (
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.HMODULE,
    ctypes.POINTER(types.LpModuleInfo),
    ctypes.wintypes.DWORD,
)


get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
get_process_memory_info.restype = ctypes.wintypes.BOOL
get_process_memory_info.argtypes = (
    ctypes.wintypes.HANDLE,
    ctypes.POINTER(types.ProcessMemoryCountersEx),
    ctypes.wintypes.DWORD,
)


get_system_info = kernel32.GetSystemInfo
get_system_info.restype = None
get_system_info.argtypes = (types.LpSystemInfo,)


read_process_memory = kernel32.ReadProcessMemory
read_process_memory.restype = ctypes.wintypes.BOOL
read_process_memory.argtypes = (
    ctypes.wintypes.HANDLE,
    ctypes.c_ulonglong,
    ctypes.wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
)


write_process_memory = kernel32.WriteProcessMemory
write_process_memory.restype = ctypes.wintypes.BOOL
write_process_memory.argtypes = (
    ctypes.wintypes.HANDLE,
    ctypes.c_ulonglong,
    ctypes.wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
)

set_last_error = kernel32.SetLastError


virtual_query_ex = kernel32.VirtualQueryEx
virtual_query_ex.argtypes = (
    ctypes.wintypes.HANDLE,
    ctypes.c_ulonglong,
    ctypes.POINTER(types.MemoryBasicInformation),
    ctypes.c_ulonglong,
)
