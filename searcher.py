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
(?:\s(?P<arch_constraint>32bit|64bit))?    # space, then optional arch constraint

""", re_VERBOSE)


_DEFAULT_FINDERS = []


ToolEntry = namedtuple('ToolEntry', ['name', 'version', 'arch', 'path'])


class VersionFilterSyntaxError(Exception):
    def __init__(self, message):
        super(VersionFilterSyntaxError, self).__init__(message)


def add_default_finder(finder):
    _DEFAULT_FINDERS.append(finder)


def get_default_finders():
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
    
    def check_name_and_arch(name, arch):
        if f_arch_constraint is not None and f_arch_constraint != arch: return False
        if name == f_name:
            return True
        return False 

    if wildcard_major and wildcard_minor:

        def _filter(name, major, minor, arch):
            return check_name_and_arch(name, arch)

    elif wildcard_major:

        def _filter(name, major, minor, arch):
            if not check_name_and_arch(name, arch): return False

            filter_pass = _filter_ver_op(minor, f_minor, f_minor_op)
            if f_minor_op2:
                filter_pass = filter_pass and _filter_ver_op(
                    minor, f_minor_op2_arg, f_minor_op2)

            return filter_pass

    elif wildcard_minor:

        def _filter(name, major, minor, arch):
            if not check_name_and_arch(name, arch): return False

            filter_pass = _filter_ver_op(major, f_major, f_major_op)
            if f_major_op2:
                filter_pass = filter_pass and _filter_ver_op(
                    major, f_major_op2_arg, f_major_op2)

            return filter_pass

    else:

        def _filter(name, major, minor, arch):
            if not check_name_and_arch(name, arch): return False

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


def compile_version_filter(version_filter):
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

            if type(ver_num) is str:
                ver_major = ver_num.split('.')
                ver_minor = int(ver_major[1])
                ver_major = int(ver_major[0])
            else:
                ver_major = ver_num[0]
                ver_minor = ver_num[1]

            for v_filter in chain:
                if v_filter(name, ver_major, ver_minor, arch):
                    output.append(entry)
        
        # sort ascending by filter priority, descending by version, descending by arch bits (64bit first)
        output.sort(key=lambda l: (
                priorities[l.name],
                -(l.version[0]+l.version[1]),
                0 if l.arch == ARCH64 else 1
            )
        )
        return output

    return _filter


class Searcher:
    def __init__(self):
        self._finders = get_default_finders()

    def add_finder(self, finder):
        self._finders.append(finder)

    def get_finders(self):
        return list(self._finders)

    def find(self, version_filter=None):
        values = set()

        for finder in self._finders:
            found = finder()
            if found:
                values.update(found)
        if version_filter:
            return compile_version_filter(version_filter)(values)
        return list(values)


def get_msbuild_paths(version_filter=None):
    return Searcher().find(version_filter=version_filter)
