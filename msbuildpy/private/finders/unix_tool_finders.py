from subprocess import check_output as proc_check_output, CalledProcessError

from msbuildpy.private.finder_util import parse_dotnetcli_msbuild_ver_output, \
    parse_msbuild_ver_output, \
    parse_xbuild_ver_output

from msbuildpy.searcher import add_default_finder

from msbuildpy.sysinspect import ARCH32, ARCH64, get_mono_vm, is_windows, is_64bit


def _unix_msbuild_paths():
    if is_windows():
        return None

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
        values += parse_msbuild_ver_output(msbuild, guess_vm_arch)

    if dotnetcli_msbuild:
        values += parse_dotnetcli_msbuild_ver_output(dotnetcli_msbuild, guess_vm_arch)

    if xbuild:
        vm_detail = get_mono_vm()
        vm_arch = vm_detail.arch if vm_detail is not None else guess_vm_arch
        values += parse_xbuild_ver_output(xbuild, vm_arch)

    return values


add_default_finder(_unix_msbuild_paths)
