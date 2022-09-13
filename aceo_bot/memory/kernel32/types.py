import ctypes
from ctypes.wintypes import WORD, DWORD, LPVOID
from typing import Iterable

from . import const


PVOID = LPVOID
SIZE_T = ctypes.c_size_t


# https://msdn.microsoft.com/en-us/library/aa383751#DWORD_PTR
if ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(ctypes.c_ulonglong):
    DWORD_PTR = ctypes.c_ulonglong
elif ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(ctypes.c_ulong):
    DWORD_PTR = ctypes.c_ulong


class LpModuleInfo(ctypes.Structure):
    """https://docs.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-enumprocessmodules"""

    _fields_ = (
        ("lpBaseOfDll", ctypes.c_ulong),
        ("SizeOfImage", DWORD),
        ("EntryPoint", PVOID),
    )


class MemoryBasicInformation(ctypes.Structure):
    """https://msdn.microsoft.com/en-us/library/aa366775"""

    _fields_ = (
        ("BaseAddress", PVOID),
        ("AllocationBase", PVOID),
        ("AllocationProtect", DWORD),
        ("RegionSize", SIZE_T),
        ("State", DWORD),
        ("Protect", DWORD),
        ("Type", DWORD),
    )

    @property
    def accessible(self):
        return all(
            [
                not self.check_permissions([const.PAGE_GUARD]),
                not self.check_permissions([const.PAGE_NOACCESS]),
                not self.check_permissions([const.PAGE_TARGETS_INVALID]),
            ]
        )

    def check_permissions(self, permissions: Iterable):
        return sum(permissions) & self.Protect


class ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = (
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    )


class SystemInfo(ctypes.Structure):
    """https://msdn.microsoft.com/en-us/library/ms724958"""

    class _U(ctypes.Union):
        class _S(ctypes.Structure):
            _fields_ = (("wProcessorArchitecture", WORD), ("wReserved", WORD))

        _fields_ = (("dwOemId", DWORD), ("_s", _S))  # obsolete
        _anonymous_ = ("_s",)

    _fields_ = (
        ("_u", _U),
        ("dwPageSize", DWORD),
        ("lpMinimumApplicationAddress", LPVOID),
        ("lpMaximumApplicationAddress", LPVOID),
        ("dwActiveProcessorMask", DWORD_PTR),
        ("dwNumberOfProcessors", DWORD),
        ("dwProcessorType", DWORD),
        ("dwAllocationGranularity", DWORD),
        ("wProcessorLevel", WORD),
        ("wProcessorRevision", WORD),
    )
    _anonymous_ = ("_u",)


LpSystemInfo = ctypes.POINTER(SystemInfo)
