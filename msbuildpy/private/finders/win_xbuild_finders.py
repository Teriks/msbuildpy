from glob import glob

from os.path import join as path_join, \
    basename as path_basename, \
    sep as path_sep, \
    isdir as path_isdir

from msbuildpy.private.finder_util import parse_xbuild_ver_output, \
    MATCH_2VER_REGEX

from msbuildpy.private.win_util import win_values_dict_reg_key, \
    win_open_reg_key_hklm

from msbuildpy.searcher import add_default_finder

from msbuildpy.sysinspect import ARCH32, ARCH64, is_windows


def _win_xbuild_path_x64():
    if not is_windows():
        return None

    try:
        with win_open_reg_key_hklm(r'SOFTWARE\Mono') as key:

            values = win_values_dict_reg_key(key)
            install_root = values.get('SdkInstallRoot', None)

            if install_root is None:
                return None

            dirs = path_join(install_root.strip(), 'lib', 'mono', 'xbuild', '*') + path_sep
            results = []

            for dir in (i for i in glob(dirs) if MATCH_2VER_REGEX.match(path_basename(i.rstrip(path_sep)))):
                bin_dir = path_join(dir, 'bin')
                if path_isdir(bin_dir):
                    results += parse_xbuild_ver_output(path_join(dir, 'bin', 'xbuild.exe'), arch=ARCH64)
            return results
    except OSError:
        return None


add_default_finder(_win_xbuild_path_x64)


def _win_xbuild_path_x86():
    if not is_windows():
        return None

    try:
        with win_open_reg_key_hklm(r'SOFTWARE\WOW6432Node\Mono') as key:

            values = win_values_dict_reg_key(key)
            install_root = values.get('SdkInstallRoot', None)
            if install_root is None: return None

            dirs = path_join(install_root.strip(), 'lib', 'mono', 'xbuild', '*') + path_sep
            results = []

            for dir in (i for i in glob(dirs) if MATCH_2VER_REGEX.match(path_basename(i.rstrip(path_sep)))):
                bin_dir = path_join(dir, 'bin')
                if path_isdir(bin_dir):
                    results += parse_xbuild_ver_output(path_join(dir, 'bin', 'xbuild.exe'), arch=ARCH32)

            return results
    except OSError:
        return None


add_default_finder(_win_xbuild_path_x86)
