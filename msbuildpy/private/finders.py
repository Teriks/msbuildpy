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


from glob import glob
from os.path import join as path_join, basename as path_basename, sep as path_sep, isdir as path_isdir
from re import compile as re_compile
from subprocess import check_output as proc_check_output, CalledProcessError

from ..searcher import add_default_finder, ToolEntry
from os import environ as os_environ

from ..inspect import ARCH32, ARCH64, get_mono_vm
from ..inspect import is_windows, is_64bit

if is_windows():
    import winreg
    from .util import win_enum_reg_key, win_dict_reg_key

_MSBUILD_VER_REGEX = re_compile(
    r'Microsoft \(R\) Build Engine version (?P<ver>[0-9]+\.[0-9]+).*')

_XBUILD_VER_REGEX = re_compile(
    r'XBuild Engine Version (?P<ver>[0-9]+\.[0-9]+)')

_MATCH_2VER_REGEX = re_compile('[0-9]+\.[0-9]+')


def _parse_msbuild_ver_output(binary_path, arch):
    version_output = proc_check_output([binary_path,
                                       '/version']).decode().strip()
    match = _MSBUILD_VER_REGEX.match(version_output)
    if match:
        version = tuple(int(x) for x in match.group('ver').split('.'))
        return [ToolEntry(name='msbuild', version=version, arch=arch, path=binary_path)]
    else:
        return []


def _parse_dotnetcli_msbuild_ver_output(binary_path, arch):
    version_output = proc_check_output([binary_path, 'build',
                                       '/version']).decode().strip()
    match = _MSBUILD_VER_REGEX.match(version_output)
    if match:
        version = tuple(int(x) for x in match.group('ver').split('.'))
        return [ToolEntry(name='dotnet build', version=version, arch=arch, path=binary_path)]
    else:
        return []


def _parse_xbuild_ver_output(binary_path, arch):
    version_output = proc_check_output([binary_path, '/version']).decode().strip()
                       
    match = _XBUILD_VER_REGEX.match(version_output)
    if match:
        version = tuple(int(x) for x in match.group('ver').split('.'))
        return [ToolEntry(name='xbuild', version=version, arch=arch, path=binary_path)]
    else:
        return []


def _env_msbuild_paths():
    values = []

    msbuild = os_environ.get('MSBUILD_PATH', None)
    xbuild = os_environ.get('XBUILD_PATH', None)

    if msbuild:
        if path_basename(msbuild).lower() == 'dotnet':
            values += _parse_dotnetcli_msbuild_ver_output(msbuild, ARCH32)
        else:
            values += _parse_msbuild_ver_output(msbuild, ARCH32)

    if xbuild:
        values += _parse_xbuild_ver_output(xbuild, ARCH32)

    return values

add_default_finder(_env_msbuild_paths)


def _other_msbuild_paths():
    if is_windows(): return None

    values = []

    dotnetcli_msbuild = None
    msbuild = None
    xbuild = None

    guess_vm_arch = ARCH64 if is_64bit() else ARCH32

    try:
        msbuild = proc_check_output(['which', 'msbuild']).decode().strip()
    except CalledProcessError:
        pass

    try:
        dotnetcli_msbuild = proc_check_output(['which',
                                              'dotnet']).decode().strip()
    except CalledProcessError:
        pass

    try:
        xbuild = proc_check_output(['which', 'xbuild']).decode().strip()
    except CalledProcessError:
        pass

    if msbuild:
        values += _parse_msbuild_ver_output(msbuild, guess_vm_arch)

    if dotnetcli_msbuild:
        values += _parse_dotnetcli_msbuild_ver_output(dotnetcli_msbuild, guess_vm_arch)

    if xbuild:
        vm_detail = get_mono_vm()
        vm_arch = vm_detail.arch if vm_detail is not None else guess_vm_arch
        values += _parse_xbuild_ver_output(xbuild, vm_arch)

    return values


add_default_finder(_other_msbuild_paths)


def _win_msbuild_paths_12_14():
    if not is_windows(): return None

    versions = ['12.0', '14.0']

    def filter_results(key, version, arch):
        return [ToolEntry(
                 name='msbuild', 
                 version=tuple(int(i) for i in version.strip().split('.')),
                 arch=arch,
                 path=path_join(x[1], r'MSBuild.exe'))
                 for x in win_enum_reg_key(key) if x[0] == 'MSBuildOverrideTasksPath']

    results = []

    for version in versions:
        try:
            with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r'SOFTWARE\Microsoft\MSBuild\{version}'.format(
                        version=version),
                    0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:

                results += filter_results(key, version, ARCH64)
        except OSError:
            pass

        try:
            with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r'SOFTWARE\WOW6432Node\Microsoft\MSBuild\{version}'
                    .format(version=version),
                    0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:

                results += filter_results(key, version, ARCH32)
        except OSError:
            pass

    return results


add_default_finder(_win_msbuild_paths_12_14)


def _win_msbuild_paths_15_x64():
    if not is_windows(): return None

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\Microsoft\VisualStudio\SxS\VS7', 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:

            return [ToolEntry(name='msbuild', 
                              version=tuple(int(i) for i in x[0].split('.')),
                              arch=ARCH64,
                              path=path_join(x[1], r'MSBuild\15.0\Bin\MSBuild.exe'))
                    for x in win_enum_reg_key(key) if x[0] == '15.0']
    except OSError:
        return None


add_default_finder(_win_msbuild_paths_15_x64)


def _win_msbuild_paths_15_x86():
    if not is_windows(): return None
    try:
        with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7', 0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:

            return [ToolEntry(name='msbuild', 
                              version=tuple(int(i) for i in x[0].split('.')),
                              arch=ARCH32,
                              path=path_join(x[1], r'MSBuild\15.0\Bin\MSBuild.exe'))
                    for x in win_enum_reg_key(key) if x[0] == '15.0']
    except OSError:
        return None


add_default_finder(_win_msbuild_paths_15_x86)


def _win_xbuild_path_x64():
    if not is_windows(): return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\Mono', 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            values = win_dict_reg_key(key)
            install_root = values.get('SdkInstallRoot', None)

            if install_root is None: return None

            dirs = path_join(install_root.strip(),'lib','mono','xbuild','*')+path_sep
            results = []

            for dir in (i for i in glob(dirs) if _MATCH_2VER_REGEX.match(path_basename(i.rstrip(path_sep)))):
                bin_dir = path_join(dir, 'bin')
                if path_isdir(bin_dir):
                    results += _parse_xbuild_ver_output(path_join(dir, 'bin', 'xbuild.exe'), arch=ARCH64)
            return results
    except OSError:
        return None
        
add_default_finder(_win_xbuild_path_x64)


def _win_xbuild_path_x86():
    if not is_windows(): return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r'SOFTWARE\WOW6432Node\Mono', 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:

            values = win_dict_reg_key(key)
            install_root = values.get('SdkInstallRoot', None)
            if install_root is None: return None

            dirs = path_join(install_root.strip(),'lib','mono','xbuild','*')+path_sep
            results = []

            for dir in (i for i in glob(dirs) if _MATCH_2VER_REGEX.match(path_basename(i.rstrip(path_sep)))):
                bin_dir = path_join(dir, 'bin')
                if path_isdir(bin_dir):
                    results += _parse_xbuild_ver_output(path_join(dir, 'bin', 'xbuild.exe'), arch=ARCH32)

            return results
    except OSError:
        return None
        
add_default_finder(_win_xbuild_path_x86)
