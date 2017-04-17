from os.path import join as path_join, \
    isfile as path_isfile

from os import environ as os_environ

from msbuildpy.private.finder_util import parse_dotnetcli_msbuild_ver_output
from msbuildpy.searcher import add_default_finder
from msbuildpy.sysinspect import ARCH32, ARCH64, is_windows


def _win_dotnetcli_msbuild():
    if not is_windows():
        return None

    program_files = os_environ["ProgramW6432"]
    program_files_x86 = os_environ["ProgramFiles(x86)"]

    cli1 = path_join(program_files, 'dotnet', 'dotnet.exe')
    cli2 = path_join(program_files_x86, 'dotnet', 'dotnet.exe')

    results = []
    if path_isfile(cli1):
        results += parse_dotnetcli_msbuild_ver_output(cli1, ARCH64)

    if path_isfile(cli2):
        results += parse_dotnetcli_msbuild_ver_output(cli2, ARCH32)

    return results


add_default_finder(_win_dotnetcli_msbuild)
