from os.path import join as path_join, \
    sep as path_sep, \
    isdir as path_isdir, \
    isfile as path_isfile, \
    dirname as path_dirname, \
    normpath as path_normpath

from msbuildpy.private.finder_util import parse_msbuild_ver_output

from msbuildpy.private.win_util import win_values_dict_reg_key, \
    win_enum_keys_reg_key, \
    win_open_reg_key_hklm, \
    win_get_drive_letters

from msbuildpy.inspect import ARCH32, ARCH64
from msbuildpy.inspect import is_windows
from msbuildpy.searcher import add_default_finder


def _win_msbuild_paths_15_default_standalone_path():
    if not is_windows():
        return

    results = []

    # This package does not have very descriptive registry entries
    # when it is installed by itself.  Check the default install path on all drives.

    for d_letter in win_get_drive_letters():

        default = d_letter + ':\\Program Files (x86)\\Microsoft Visual ' \
                             'Studio\\2017\\BuildTools\\MSBuild\\15.0\\Bin\\MSBuild.exe'

        if path_isfile(default):
            results += parse_msbuild_ver_output(default, ARCH32)

        default = d_letter + ':\\Program Files\\Microsoft Visual ' \
                             'Studio\\2017\\BuildTools\\MSBuild\\15.0\\Bin\\MSBuild.exe'

        if path_isfile(default):
            results += parse_msbuild_ver_output(default, ARCH64)

    return results

add_default_finder(_win_msbuild_paths_15_default_standalone_path)


def _win_visual_studios_2017_fingerprint_edition(install_root):
    if path_isdir(path_join(install_root,'Common7','IDE','Extensions','Enterprise')):
        return 'enterprise'
    if path_isdir(path_join(install_root,'Common7','IDE','Extensions','Professional')):
        return 'professional'
    if path_isdir(path_join(install_root,'Common7','IDE','Extensions','Community')):
        return 'community'
    return None


def _win_msbuild_paths_15_read_app_id_keys(base_key, key, arch):

    for subkey in win_enum_keys_reg_key(key):
        if not subkey.startswith('VisualStudio_'):
            continue
        try:
            with win_open_reg_key_hklm(base_key+'\\'+subkey+'\\Capabilities') as cap_key:

                value_dict = win_values_dict_reg_key(cap_key)
                app_name = value_dict.get('ApplicationName', None)
                if app_name and not app_name.startswith('Microsoft Visual Studio 2017'):
                    continue
                app_desc = value_dict.get('ApplicationDescription', None)
                if not app_desc:
                    continue

                install_root = path_normpath(path_join(app_desc.lstrip('@'), '..', '..', '..'))
                msbuild_dir = 'MSBuild\\15.0\\Bin\\MSBuild.exe'
                msbuild = path_join(install_root, msbuild_dir)

                if path_isfile(msbuild):
                    result = parse_msbuild_ver_output(
                        msbuild, arch,
                        edition=_win_visual_studios_2017_fingerprint_edition(install_root)
                    )
                    if len(result):
                        yield result[0]

        except OSError:
            pass


def _win_msbuild_paths_15_reg_by_app_id_x86():
    if not is_windows():
        return

    # check the VisualStudio_{HASH} registry keys to try to derive
    # install locations from the devenvdesc.dll path

    base_key = r'SOFTWARE\WOW6432Node\Microsoft'
    try:
        with win_open_reg_key_hklm(base_key) as key:
            return list(_win_msbuild_paths_15_read_app_id_keys(base_key, key, ARCH32))
    except OSError:
        return None

    return None


add_default_finder(_win_msbuild_paths_15_reg_by_app_id_x86)


def _win_msbuild_paths_15_read_reg_sxs_key(key, arch):
    reg_values = win_values_dict_reg_key(key)
    path = reg_values.get('15.0', None)
    results = []

    if path:
        msbuild_dir = 'MSBuild\\15.0\\Bin\\MSBuild.exe'
        common_dir = path_dirname(path.rstrip(path_sep))

        # stand alone build tools
        buildtools = path_join(common_dir, 'BuildTools', msbuild_dir)
        if path_isfile(buildtools):
            results += parse_msbuild_ver_output(buildtools, arch)

        community = path_join(common_dir, 'Community', msbuild_dir)
        if path_isfile(community):
            results += parse_msbuild_ver_output(community, arch, edition='community')

        professional = path_join(common_dir, 'Professional', msbuild_dir)
        if path_isfile(professional):
            results += parse_msbuild_ver_output(professional, arch, edition='professional')

        enterprise = path_join(common_dir, 'Enterprise', msbuild_dir)
        if path_isfile(enterprise):
            results += parse_msbuild_ver_output(enterprise, arch, edition='enterprise')

    return results


def _win_msbuild_paths_15_sxs_x64():
    if not is_windows():
        return None

    try:
        with win_open_reg_key_hklm(r'SOFTWARE\Microsoft\VisualStudio\SxS\VS7') as key:

            return _win_msbuild_paths_15_read_reg_sxs_key(key, ARCH64)
    except OSError:
        return None


add_default_finder(_win_msbuild_paths_15_sxs_x64)


def _win_msbuild_paths_15_sxs_x86():
    if not is_windows():
        return None

    try:
        with win_open_reg_key_hklm(r'SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7') as key:

            return _win_msbuild_paths_15_read_reg_sxs_key(key, ARCH32)
    except OSError:
        return None


add_default_finder(_win_msbuild_paths_15_sxs_x86)