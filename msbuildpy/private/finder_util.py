from msbuildpy.searcher import ToolEntry
from re import compile as re_compile
from subprocess import check_output as proc_check_output

_MSBUILD_VER_REGEX = re_compile(
    r'Microsoft \(R\) Build Engine version (?P<ver>[0-9]+\.[0-9]+).*')

_XBUILD_VER_REGEX = re_compile(
    r'XBuild Engine Version (?P<ver>[0-9]+\.[0-9]+)')


MATCH_2VER_REGEX = re_compile('[0-9]+\.[0-9]+')


def parse_msbuild_ver_output(binary_path, arch, edition=None):
    version_output = proc_check_output([binary_path,
                                        '/version']).decode().strip()
    match = _MSBUILD_VER_REGEX.match(version_output)
    if match:
        version = tuple(int(x) for x in match.group('ver').split('.'))
        return [ToolEntry(name='msbuild', version=version, arch=arch, edition=edition, path=binary_path)]
    else:
        return []


def parse_dotnetcli_msbuild_ver_output(binary_path, arch, edition=None):
    version_output = proc_check_output([binary_path, 'build',
                                        '/version']).decode().strip()
    match = _MSBUILD_VER_REGEX.match(version_output)
    if match:
        version = tuple(int(x) for x in match.group('ver').split('.'))
        return [ToolEntry(name='dotnet build', version=version, arch=arch, edition=edition, path=binary_path)]
    else:
        return []


def parse_xbuild_ver_output(binary_path, arch):
    version_output = proc_check_output([binary_path, '/version']).decode().strip()

    match = _XBUILD_VER_REGEX.match(version_output)
    if match:
        version = tuple(int(x) for x in match.group('ver').split('.'))
        return [ToolEntry(name='xbuild', version=version, arch=arch, edition=None, path=binary_path)]
    else:
        return []