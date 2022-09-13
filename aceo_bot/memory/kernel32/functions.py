import ctypes

from . import kernel32, types
from .decorators import raise_on_error


@raise_on_error
def get_system_info() -> types.SystemInfo:
    system_info = types.SystemInfo()
    kernel32.get_system_info(ctypes.byref(system_info))
    return system_info


@raise_on_error
def get_process_memory_info(handle):
    memory_counters_ex = types.ProcessMemoryCountersEx()
    kernel32.get_process_memory_info(handle, ctypes.byref(memory_counters_ex), ctypes.sizeof(memory_counters_ex))
    return memory_counters_ex


@raise_on_error
def read_process_memory(handle, address, size) -> bytes:
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    if not kernel32.read_process_memory(handle, address, buffer, size, ctypes.byref(bytes_read)):
        return b""
    return buffer.raw


@raise_on_error
def get_module_handle(module: str):
    module_handle = kernel32.get_module_handle(module.encode())
    if not module_handle:
        return b""
    return module_handle


@raise_on_error
def read_process_module_base_address(handle, module_handle) -> types.LpModuleInfo:
    info = types.LpModuleInfo()
    if not kernel32.get_module_base_address(handle, module_handle, ctypes.byref(info), ctypes.sizeof(info)):
        return b""
    return info


@raise_on_error
def virtual_query_ex(handle, address) -> types.MemoryBasicInformation:
    info = types.MemoryBasicInformation()
    kernel32.virtual_query_ex(handle, address, ctypes.byref(info), ctypes.sizeof(info))
    return info


@raise_on_error
def write_process_memory(handle, address, data: bytes) -> bool:
    buffer = ctypes.create_string_buffer(data)
    bytes_written = ctypes.c_size_t(0)
    kernel32.write_process_memory(handle, address, buffer, len(data), ctypes.byref(bytes_written))
    return bytes_written.value
