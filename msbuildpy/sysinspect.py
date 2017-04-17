# Copyright (c) 2017, Teriks
#
# msbuildpy is distributed under the following BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
Contains tools for inspecting system architecture/host OS, and finding mono VM's.
"""

from functools import lru_cache
from os.path import join as path_join
from platform import system as platform_system, machine as platform_machine
from re import compile as re_compile
from subprocess import check_output as proc_check_output

from collections import namedtuple

from .private.win_util import win_values_dict_reg_key

ARCH32 = '32bit'
"""
Signifies 32bit architecture, is equal to '32bit'.
"""

ARCH64 = '64bit'
"""
Signifies 64bit architecture, is equal to '64bit'.
"""

_PLATFORM = platform_system().lower()

_MACHINE = platform_machine()

_ON_WINDOWS = _PLATFORM == 'windows'
_ON_LINUX = _PLATFORM == 'linux' or _PLATFORM == 'linux2'
_ON_MAC = _PLATFORM == 'darwin' or _PLATFORM == 'macosx'
_ON_OPENBSD = _PLATFORM == 'openbsd'
_ON_FREEBSD = _PLATFORM == 'freebsd'
_ON_NETBSD = _PLATFORM == 'netbsd'

_MACHINE_BITS_MAP = {
    'AMD64': ARCH64,
    'IA64': ARCH64,
    'x86_64': ARCH64,
    'i386': ARCH32,
    'x86': ARCH32
}


def _machine_bits_rest(machine):
    if _ON_LINUX or _ON_MAC:
        try:
            bits = proc_check_output(['getconf', 'LONG_BIT']).decode().strip()
            return ARCH64 if bits == '64' else ARCH32
        except OSError:
            pass

    return None


_MONO_OUTPUT_ARCH_REGEX = re_compile('Architecture:\s*(?P<arch>.+)')

_MONO_ARCH_MAP = {
    'amd64': ARCH64,
    'arm': ARCH32,
    'armel,vfp+hard': ARCH32,
    'arm64': ARCH64,
    'ia64': ARCH64,
    'x86': ARCH32
}


def _mono_arch_rest(ver_architecure):
    return ARCH64 if is_64bit() else ARCH32


def is_windows():
    """
    Test if the underlying OS is Windows.
    
    :return: bool 
    """
    return _ON_WINDOWS


def is_linux():
    """
    Test if the underlying OS is Linux.
    
    :return: bool
    """
    return _ON_LINUX


def is_mac():
    """
    Test if the underlying OS is Mac OS.
    
    :return: bool
    """
    return _ON_MAC


def is_openbsd():
    """
    Test if the underlying OS is OpenBSD.
    
    :return: bool
    """
    return _ON_OPENBSD


def is_freebsd():
    """
    Test if the underlying OS is FreeBSD.
    
    :return: bool
    """
    return _ON_FREEBSD


def is_netbsd():
    """
    Test if the underlying OS is NetBSD.
    
    :return: bool
    """
    return _ON_NETBSD


@lru_cache(maxsize=None)
def is_32bit():
    """
    Test if the underlying OS/Machine is 32bit.
    
    :return: bool
    """

    bits = _MACHINE_BITS_MAP.get(_MACHINE, None)
    if bits:
        return bits == ARCH32

    bits = _machine_bits_rest(_MACHINE)
    if bits:
        return bits == ARCH32

    raise NotImplementedError('unknown machine type')


@lru_cache(maxsize=None)
def is_64bit():
    """
    Test if the underlying OS/Machine is 64bit.
    
    :return: bool
    """

    bits = _MACHINE_BITS_MAP.get(_MACHINE, None)
    if bits:
        return bits == ARCH64

    bits = _machine_bits_rest(_MACHINE)
    if bits:
        return bits == ARCH32

    raise NotImplementedError('unknown machine type')


def get_arch():
    """
    Get the architecture of the underlying OS/Machine
    
    :return: :py:const:`msbuildpy.sysinspect.ARCH64` or :py:const:`msbuildpy.sysinspect.ARCH32`
    """

    return ARCH32 if is_32bit() else ARCH64


class MonoVm(namedtuple('MonoVm', ['version', 'arch', 'path'])):
    """
    Represents a Mono VM binary, with version, architecture and binary path.
    
    :var version: Version tuple (major, minor, patch)
    :var arch: Architecture, :py:const:`msbuildpy.sysinspect.ARCH64` or :py:const:`msbuildpy.sysinspect.ARCH32`
    :var path: Full path to the binary, (a string).
    """


def _win_read_mono_vm_from_registry_key(key, arch):
    values = win_values_dict_reg_key(key)
    install_root = values.get('SdkInstallRoot', None)
    version = values.get('Version', None)
    if install_root is None or version is None: return None

    return MonoVm(
        tuple(int(i) for i in version.split('.')),
        arch,
        path_join(install_root, 'bin', 'mono.exe')
    )


def _win_get_mono_vm_x64():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\Mono', 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return _win_read_mono_vm_from_registry_key(key, ARCH64)
    except OSError:
        return None


def _win_get_mono_vm_x86():
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\WOW6432Node\Mono', 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return _win_read_mono_vm_from_registry_key(key, ARCH32)
    except OSError:
        return None


def _other_get_mono_vm():
    try:
        version = proc_check_output(["mono", "--version"]).decode()

        arch_match = _MONO_OUTPUT_ARCH_REGEX.search(version)

        if arch_match is None:
            arch = ARCH64 if is_64bit() else ARCH32
        else:
            arch = arch_match.group('arch')

            arch = _MONO_ARCH_MAP.get(arch, None)

            if arch is None:
                arch = _mono_arch_rest(arch)

        version = version[26:]
        version = tuple(int(i) for i in version[:version.find(' ')].split("."))
        path = proc_check_output(['which', 'mono']).decode().strip()

        return MonoVm(version, arch, path)
    except OSError:
        return None


@lru_cache(maxsize=None)
def get_mono_vm(arch=None):
    """
    Try to find a Mono VM binary.  If architecture is not specified, this function
    will prioritize returning a 64bit VM over a 32bit VM if both are installed.
    
    Returns **None** if no VM is found.
    
    :param arch: Architecture, :py:const:`msbuildpy.sysinspect.ARCH64` or :py:const:`msbuildpy.sysinspect.ARCH32`
    
    :return: :py:class:`msbuildpy.sysinspect.MonoVm` or **None**
    """
    if arch is None:
        if is_windows():
            r = _win_get_mono_vm_x64()
            if r is None:
                return _win_get_mono_vm_x86()
            return r
        return _other_get_mono_vm()

    if arch == ARCH32:
        if is_windows():
            return _win_get_mono_vm_x86()
        if is_64bit():
            return None
        return _other_get_mono_vm()

    if arch == ARCH64:
        if is_windows():
            return _win_get_mono_vm_x64()
        if is_32bit():
            return None
        return _other_get_mono_vm()
