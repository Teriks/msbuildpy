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


import collections
import re
from importlib import import_module

from . import sysinspect
from . import version

_FILTER_REGEX = re.compile("""
^
(?P<name>[-a-zA-Z_ ]+)?\s+ # tool name
(?P<version_constraint>{version_constraint})? # version constraint
(?:\s+(?P<arch_constraint>32bit|64bit))?   # space, then optional arch constraint
(?:\s+(?P<edition_constraint>[a-zA-Z]+))?  # space, then optional edition constraint
$
""".format(version_constraint=version.VERSION_CONSTRAINT_REGEX_STR), re.VERBOSE)

_DEFAULT_FINDERS = []

EDITION_COMMUNITY = 'community'
"""
Signifies VS Community edition
"""

EDITION_PROFESSIONAL = 'professional'
"""
Signifies VS Professional edition
"""

EDITION_ENTERPRISE = 'enterprise'
"""
Signifies VS Enterprise edition
"""

EDITION_STANDALONE = 'standalone'
"""
Signifies VS Standalone edition
"""


class ToolEntry(collections.namedtuple('ToolEntry', ['name', 'version', 'arch', 'edition', 'path'])):
    """
    Represents an MSBuild tool binary/location.
    
    Architecture is dependent on the architecture of the tool install.
    
    On Unix like systems architecture most likely aligns to the OS architecture.
    But on Windows, Microsoft distributes MSBuild 12 and 14 in separate x86 and x64 versions.
    
    MSBuild 15 on windows (VS2017) only installs an x86 built version.
    
    MSBuild 15 on windows is currently the only tool which populates the 'edition' attribute.
    
    :var name: Tool name. ie 'msbuild', 'xbuild' or 'dotnet build'
    :var version: Version tuple of varying size (major, minor, ...)
    :var arch: Architecture of tool installation, :py:const:`msbuildpy.sysinspect.ARCH64` or :py:const:`msbuildpy.sysinspect.ARCH32`
    :var edition: Visual Studio's edition if applicable: 'community', 'professional', 'enterprise' or 'standalone'
    :var path: Full path to the binary, (a string).
    """


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


def _compile_single_ver_filter(v_filter):
    parsed_filter = _FILTER_REGEX.match(v_filter.strip())

    if parsed_filter is None:
        raise version.VersionFilterSyntaxError(
            'Syntax error in filter: "{filter}"'.format(filter=v_filter))

    f_name = parsed_filter.group('name').strip()
    f_version_constraint = parsed_filter.group('version_constraint')
    f_arch_constraint = parsed_filter.group('arch_constraint')
    f_edition_constraint = parsed_filter.group('edition_constraint')

    if f_version_constraint:
        version_match = version.compile_matcher(f_version_constraint)

        def _filter(tool_entry):
            match = tool_entry.name == f_name and version_match(tool_entry.version)
            if f_arch_constraint:
                match = match and tool_entry.arch == f_arch_constraint
            if f_edition_constraint:
                match = match and tool_entry.edition == f_edition_constraint
            return not match
    else:
        def _filter(tool_entry):
            match = tool_entry.name == f_name
            if f_arch_constraint:
                match = match and tool_entry.arch == f_arch_constraint
            if f_edition_constraint:
                match = match and tool_entry.edition == f_edition_constraint
            return not match

    return f_name, _filter


_VS_EDITION_PRIORITY_MAP = {
    'community': 1,
    'professional': 2,
    'enterprise': 3,
    'ultimate': 3,
    'standalone': 4
}


def _vs_edition_priority(edition):
    if edition is None:
        return 5

    edition = edition.lower()

    p = _VS_EDITION_PRIORITY_MAP.get(edition, None)
    if p is not None:
        return p

    assert False, "Unknown edition string returned in search: {edition}".format(edition=edition)


def compile_tool_filter(tool_filter):
    """
    Compile a version filter function which acts on a list of :py:class:`msbuildpy.ToolEntry` objects.
    
    See: :py:func:`msbuildpy.find_msbuild` for **tool_filter** examples.
    
    :param tool_filter: Version filter string.
    :return: A function accepting a list of :py:class:`msbuildpy.ToolEntry` objects.
    """
    filter_ors = tool_filter.strip().split('|')

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
            for v_filter in chain:
                if not v_filter(entry):
                    output.append(entry)

        # sort ascending by filter priority, descending by version, descending by arch bits (64bit first)
        output.sort(key=lambda l: (
            priorities[l.name],
            -(l.version[0] + l.version[1]),
            0 if l.arch == sysinspect.ARCH64 else 1,
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

    def find(self, tool_filter=None):
        """
        Find msbuild tools on the system using the finders in this Searcher object.
        
        See: :py:func:`msbuildpy.find_msbuild` for **tool_filter** examples.
        
        :param tool_filter: Version filter string
    
        :return: A list of :py:class:`msbuildpy.ToolEntry` objects, which may be empty.
        """
        values = set()

        for finder in self._finders:
            found = finder()
            if found:
                values.update(found)
        if tool_filter:
            return compile_tool_filter(tool_filter)(values)
        return list(values)


def find_msbuild(tool_filter=None):
    """
        Find msbuild tools on the system, using an optional version filter.
    
        See: :py:func:`msbuildpy.version.compile_matcher` for more version match
        expression examples.  It is used for compile the version matchers used to
        match version numbers in tool filter expressions.
        
        Tool Filter Examples:
    
    .. code-block:: python
    
        # Version matching supports wildcards for major and minor version components.
        # OR expressions are also supported.
        
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
        
        # Get the standalone build tools if they are installed
        
        find_msbuild('msbuild 15.* standalone')
        
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
    
    Tools that report an edition of **None** or **'standalone'** have a higher value than named editions, so they
    come last in the output.
        
    :param tool_filter: Version filter string
    
    :return: A list of :py:class:`msbuildpy.ToolEntry` objects, which may be empty.
    """

    return Searcher().find(tool_filter=tool_filter)


import_module('msbuildpy.private.finders_entrypoint')
