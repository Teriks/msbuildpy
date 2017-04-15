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


from re import compile as re_compile, VERBOSE as re_VERBOSE

from collections import namedtuple

from .inspect import ARCH64

_FILTER_REGEX = re_compile(r"""

(?P<name>[-a-zA-Z_ ]+)?         # name
(?P<major_operator><=|>=|<|>)?  # first major version constraint
\s*
(?P<major>\*|[*0-9]+)           # major version number
\s*
(?:(?P<major_operator2><=|>=|<|>)\s*(?P<major_operator2_arg>[*0-9]+))?  # second major version constraint, with integer parameter
\s*

\.  # version seperator

(?P<minor_operator><=|>=|<|>)?  # first minor version constraint
\s*
(?P<minor>\*|[0-9]+)   # minor version number
\s*?
(?:(?P<minor_operator2><=|>=|<|>)\s*(?P<minor_operator2_arg>[*0-9]+))?  # second minor version constraint, with integer parameter
(?:\s(?P<arch_constraint>32bit|64bit))?   # space, then optional arch constraint
(?:\s(?P<edition_constraint>[a-zA-Z]+))?  # space, then optional edition constraint
""", re_VERBOSE)


_DEFAULT_FINDERS = []


class ToolEntry(namedtuple('ToolEntry', ['name', 'version', 'arch', 'edition', 'path'])):
    """
    Represents an MSBuild tool binary/location.
    
    Architecture is dependent on the architecture of the tool install.
    
    On Unix like systems architecture most likely aligns to the OS architecture.
    But on Windows, Microsoft distributes MSBuild 12 and 14 in separate x86 and x64 versions.
    
    MSBuild 15 on windows (VS2017) only installs an x86 built version.
    
    MSBuild 15 on windows is currently the only tool which populates the 'edition' attribute.
    
    :var name: Tool name. ie 'msbuild', 'xbuild' or 'dotnet build'
    :var version: Version tuple (major, minor)
    :var arch: Architecture of tool installation, :py:const:`msbuildpy.inspect.ARCH64` or :py:const:`msbuildpy.inspect.ARCH32`
    :var edition: Visual Studio's edition if applicable: 'community', 'professional' or 'enterprise'
    :var path: Full path to the binary, (a string).
    """


class VersionFilterSyntaxError(Exception):
    """
    Raised by :py:func:`msbuildpy.compile_version_filter` if there is a syntax
    error in the version filter expression provided to it.
    """
    def __init__(self, message):
        super(VersionFilterSyntaxError, self).__init__(message)


def add_default_finder(finder):
    """
    Add a default finder function.
    
    Finder functions should return a list of :py:class:`msbuildpy.ToolEntry` objects, or **None**
    
    :param finder: A function accepting no arguments.
    """
    _DEFAULT_FINDERS.append(finder)


def get_default_finders():
    """
    Get default finder functions.
    
    See: :py:func:`msbuildpy.add_default_finder`
    
    :return: Copied list of default finder functions.
    """
    return list(_DEFAULT_FINDERS)


def _filter_ver_op(version_l, version_r, op):
    l = int(version_l)
    r = int(version_r)
    if op is None:
        return l == r
    if op == '>=':
        return l >= r
    if op == '>':
        return l > r
    if op == '<=':
        return l <= r
    if op == '<':
        return l < r


def _compile_single_ver_filter(v_filter):
    match = _FILTER_REGEX.match(v_filter.strip())

    if match is None:
        raise VersionFilterSyntaxError(
            'Syntax error in filter: "{filter}"'.format(filter=v_filter))

    f_name = match.group('name').strip()
    f_major = match.group('major').strip()
    f_minor = match.group('minor').strip()
    f_major_op = match.group('major_operator')
    f_minor_op = match.group('minor_operator')
    f_major_op2 = match.group('major_operator2')
    f_minor_op2 = match.group('minor_operator2')
    f_major_op2_arg = match.group('major_operator2_arg')
    f_minor_op2_arg = match.group('minor_operator2_arg')
    f_arch_constraint = match.group('arch_constraint')
    f_edition_constraint = match.group('edition_constraint')

    if f_major_op:
        f_major_op = f_major_op.strip()
    if f_minor_op:
        f_minor_op = f_minor_op.strip()

    if f_major_op2:
        if not f_major_op:
            msg = 'Cannot use the second operator syntax on the major version number without using the first operator.'
            raise VersionFilterSyntaxError(
                'Syntax error in filter: "{filter}"\n{msg}'.format(
                    filter=v_filter, msg=msg))

        f_major_op2 = f_major_op2.strip()
        f_major_op2_arg = f_major_op2_arg.strip()

    if f_minor_op2:
        if not f_minor_op:
            msg = 'Cannot use the second operator syntax on the minor version number without using the first operator.'
            raise VersionFilterSyntaxError(
                'Syntax error in filter: "{filter}"\n{msg}'.format(
                    filter=v_filter, msg=msg))

        f_minor_op2 = f_minor_op2.strip()
        f_minor_op2_arg = f_minor_op2_arg.strip()

    wildcard_major = f_major == '*'
    wildcard_minor = f_minor == '*'
    
    def check_exacts(name, arch, edition):
        edition = edition.lower() if edition is not None else None

        if f_arch_constraint is not None and f_arch_constraint != arch:
            return False
        if f_edition_constraint is not None and f_edition_constraint.lower() != edition:
            return False
        if name == f_name:
            return True
        return False 

    if wildcard_major and wildcard_minor:

        def _filter(name, major, minor, arch, edition):
            return check_exacts(name, arch, edition)

    elif wildcard_major:

        def _filter(name, major, minor, arch, edition):
            if not check_exacts(name, arch, edition):
                return False

            filter_pass = _filter_ver_op(minor, f_minor, f_minor_op)
            if f_minor_op2:
                filter_pass = filter_pass and _filter_ver_op(
                    minor, f_minor_op2_arg, f_minor_op2)

            return filter_pass

    elif wildcard_minor:

        def _filter(name, major, minor, arch, edition):
            if not check_exacts(name, arch, edition):
                return False

            filter_pass = _filter_ver_op(major, f_major, f_major_op)
            if f_major_op2:
                filter_pass = filter_pass and _filter_ver_op(
                    major, f_major_op2_arg, f_major_op2)

            return filter_pass

    else:

        def _filter(name, major, minor, arch, edition):
            if not check_exacts(name, arch, edition):
                return False

            filter_pass = _filter_ver_op(minor, f_minor,
                                         f_minor_op) and _filter_ver_op(
                                             major, f_major, f_major_op)

            if f_major_op2:
                filter_pass = filter_pass and _filter_ver_op(
                    major, f_major_op2_arg, f_major_op2)
            if f_minor_op2:
                filter_pass = filter_pass and _filter_ver_op(
                    minor, f_minor_op2_arg, f_minor_op2)
            return filter_pass

    return (f_name, _filter)


_VS_EDITION_PRIORITY_MAP = {
    'community': 0,
    'professional': 1,
    'enterprise': 2,
    'ultimate': 2
}


def _vs_edition_priority(edition):
    if edition is None:
        return 0

    edition = edition.lower()

    p = _VS_EDITION_PRIORITY_MAP.get(edition, None)
    if p is not None:
        return p

    assert False, "Unknown edition string returned in search: {edition}".format(edition=edition)


def compile_version_filter(version_filter):
    """
    Compile a version filter function which acts on a list of :py:class:`msbuildpy.ToolEntry` objects.
    
    See: :py:func:`msbuildpy.find_msbuild` for **version_filter** examples.
    
    :param version_filter: Version filter string.
    :return: A function accepting a list of :py:class:`msbuildpy.ToolEntry.ToolEntry` objects.
    """
    filter_ors = version_filter.strip().split('|')

    priorities = dict()

    chain = []

    for idx, filter_or in enumerate(filter_ors):
        filter_name, compiled_filter = _compile_single_ver_filter(filter_or)
        if filter_name not in priorities:
            priorities[filter_name] = idx
        chain.append(compiled_filter)

    def _filter(entries):
        output = []
        for entry in entries:
            name = entry.name
            ver_num = entry.version
            arch = entry.arch
            edition = entry.edition

            if type(ver_num) is str:
                ver_major = ver_num.split('.')
                ver_minor = int(ver_major[1])
                ver_major = int(ver_major[0])
            else:
                ver_major = ver_num[0]
                ver_minor = ver_num[1]

            for v_filter in chain:
                if v_filter(name, ver_major, ver_minor, arch, edition):
                    output.append(entry)
        
        # sort ascending by filter priority, descending by version, descending by arch bits (64bit first)
        output.sort(key=lambda l: (
                priorities[l.name],
                -(l.version[0]+l.version[1]),
                0 if l.arch == ARCH64 else 1,
                _vs_edition_priority(l.edition)
            )
        )
        return output

    return _filter


class Searcher:
    """
    Tool searcher in object form.  Allows additional finders to be associated
    with an object instead of with the module globally.
    
    The searcher object is populated with the default finder functions in the module when **use_default_finders=True**
    """
    def __init__(self, use_default_finders=True):
        """
        Init the searcher, populate it with :py:func:`msbuildpy.get_default_finders` unless **use_default_finders**
        is set to **False**.
        
        :param use_default_finders: bool, whether to populate the searcher with the modules default finder functions. 
        """
        if use_default_finders:
            self._finders = get_default_finders()
        else:
            self._finders = []

    def add_finder(self, finder):
        """
        Add a finder function.
        
        Finder functions should return a list of :py:class:`msbuildpy.ToolEntry` objects, or **None**
        
        :param finder: A function accepting no arguments.
        """
        self._finders.append(finder)

    def get_finders(self):
        """
        Get finder functions.
        
        See: :py:func:`msbuildpy.add_default_finder`
        
        :return: Copied list of finder functions in this Searcher.
        """
        return list(self._finders)

    def find(self, version_filter=None):
        """
        Find msbuild tools on the system using the finders in this Searcher object.
        
        See: :py:func:`msbuildpy.find_msbuild` for **version_filter** examples.
        
        :param version_filter: Version filter string
    
        :return: A list of :py:class:`msbuildpy.ToolEntry` objects, which may be empty.
        """
        values = set()

        for finder in self._finders:
            found = finder()
            if found:
                values.update(found)
        if version_filter:
            return compile_version_filter(version_filter)(values)
        return list(values)


def find_msbuild(version_filter=None):
    """
        Find msbuild tools on the system, using an optional version filter.
    
        Version Filter Examples:
    
    .. code-block:: python
    
        # supports wildcards for major and minor version components.
        # OR expressions are also supported.  You must provide the major
        # and minor version component,  leaving out the . separator is a 
        # syntax error.
        
        find_msbuild('msbuild 12.* | xbuild >=12.* | dotnet build *.*')
        
        # operators against version numbers include (>= | <= | > | <)
        # operators can come before and after each version component 
        # to specify a limited range
        
        find_msbuild('msbuild >=12.* | xbuild >=12<15.*')
        
        # architecture can be specified
        
        find_msbuild('msbuild 12.* 64bit | msbuild 14.* 32bit')
        
        # edition can be specified, with or without architecture
        # this only really applies to Microsofts build tool
        
        # MSBuild 12 and 14 on windows do not currently return an edition
        #
        # (Not Implemented yet, unsure if needed.  All of the editions may use
        #  the same tool, I have not checked yet)
        #
        # So their ToolEntry's will always have: edition = **None**
        
        find_msbuild('msbuild 15.* professional | msbuild 15.* community')
        
        # With architecture. (Note, edition is not case sensitive)
        
        find_mbuild('msbuild 15.* 32bit Enterprise')
        
        # singular request example, with exact version match
        # as well as architecture specified.
        
        find_msbuild('msbuild 14.0 64bit')
        
        # find the dotnet cli build tool
        
        find_msbuild('dotnet build 15.*')
        
        
    The version filter sorts the tool entries ascending by filter priority (their OR chain order),
    then descending by version, then descending by arch bits (64bit comes first), then ascending by edition.
    
    A tool entries first appearance in the filter sets the sort priority of the tool.
    
    If there are OR expressions, tools at the beginning will be first in the output if they exist.
    
    The 'edition' attribute of :py:class:`msbuildpy.ToolEntry` is sorted in ascending order, aka:
    by the quantity of money you are paying Microsoft for Visual Studios.
    
    Tools that report an 'edition' of **None** have have a lower value than 'community' editions, so they
    come before them.
        
    :param version_filter: Version filter string
    
    :return: A list of :py:class:`msbuildpy.ToolEntry` objects, which may be empty.
    """

    return Searcher().find(version_filter=version_filter)
