from os.path import join as path_join

from msbuildpy.private.win_util import win_open_reg_key_hklm, \
    win_enum_values_reg_key

from msbuildpy.searcher import add_default_finder

from msbuildpy.sysinspect import ARCH32, ARCH64, is_windows

from msbuildpy.private.finder_util import parse_msbuild_ver_output


def _win_msbuild_paths_12_14():
    if not is_windows():
        return None

    versions = ['12.0', '14.0']

    def filter_results(key, arch):

        for key_name, key_value in win_enum_values_reg_key(key):
            if key_name == 'MSBuildOverrideTasksPath':
                return parse_msbuild_ver_output(path_join(key_value, r'MSBuild.exe'), arch)

    results = []

    for version in versions:
        try:
            with win_open_reg_key_hklm(
                    r'SOFTWARE\Microsoft\MSBuild\{version}'.format(version=version)
            ) as key:

                results += filter_results(key, ARCH64)
        except OSError:
            pass

        try:
            with win_open_reg_key_hklm(
                    r'SOFTWARE\WOW6432Node\Microsoft\MSBuild\{version}'.format(version=version)
            ) as key:

                results += filter_results(key, ARCH32)
        except OSError:
            pass

    return results


add_default_finder(_win_msbuild_paths_12_14)
