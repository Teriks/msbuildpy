from os.path import join as path_join

from msbuildpy.private.win_util import win_open_reg_key_hklm, \
    win_enum_values_reg_key

from msbuildpy.inspect import ARCH32, ARCH64
from msbuildpy.inspect import is_windows
from msbuildpy.searcher import add_default_finder, ToolEntry


def _win_msbuild_paths_12_14():
    if not is_windows():
        return None

    versions = ['12.0', '14.0']

    def filter_results(key, version, arch):
        return [ToolEntry(
            name='msbuild',
            version=tuple(int(i) for i in version.strip().split('.')),
            arch=arch,
            edition=None,
            path=path_join(x[1], r'MSBuild.exe'))
            for x in win_enum_values_reg_key(key) if x[0] == 'MSBuildOverrideTasksPath']

    results = []

    for version in versions:
        try:
            with win_open_reg_key_hklm(
                    r'SOFTWARE\Microsoft\MSBuild\{version}'.format(version=version)
            ) as key:

                results += filter_results(key, version, ARCH64)
        except OSError:
            pass

        try:
            with win_open_reg_key_hklm(
                    r'SOFTWARE\WOW6432Node\Microsoft\MSBuild\{version}'.format(version=version)
            ) as key:

                results += filter_results(key, version, ARCH32)
        except OSError:
            pass

    return results


add_default_finder(_win_msbuild_paths_12_14)