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


"""
Version string matcher function compilation
"""

import functools
import re


class VersionFilterSyntaxError(Exception):
    """
    Raised if there is a syntax error in a version filter expression.
    """

    def __init__(self, message):
        super(VersionFilterSyntaxError, self).__init__(message)


_OP_REGEX_STR = '(?:<=|>=|<|>)'
_COMPONENT_REGEX_STR = '(?:[0-9]+|\*)'

_REMOVE_SPACE_REGEX = re.compile(r"\s+", flags=re.UNICODE)

VERSION_CONSTRAINT_REGEX_STR = \
    '{ver_ops}?\s*{component}+\s*(?:{ver_ops}\s*[0-9]+)?\s*(?:\.\s*{ver_ops}?\s*{component}+\s*(?:{ver_ops}\s*[0-9]+)?)*' \
        .format(ver_ops=_OP_REGEX_STR, component=_COMPONENT_REGEX_STR)
"""
A string containing a regex which matches a version constraint expression used by :py:func:`msbuildpy.version.compile_matcher`.
The regex in the string does not have ^$ anchors.
"""

_VERSION_CONSTRAINT_COMPONENT_REGEX = re.compile("""
(?P<op_one>{ver_ops})? # first operator
(?P<component>{component}) # component
(?:(?P<op_two>{ver_ops})(?P<op_two_arg>[0-9]+))?
""".format(ver_ops=_OP_REGEX_STR, component=_COMPONENT_REGEX_STR), re.VERBOSE)


def _op_lt(l, r):
    return l < r


def _op_gt(l, r):
    return l > r


def _op_lte(l, r):
    return l <= r


def _op_gte(l, r):
    return l >= r


_OPERATORS = {
    '<': _op_lt,
    '>': _op_gt,
    '<=': _op_lte,
    '>=': _op_gte
}


def _get_operator(operator):
    return _OPERATORS[operator]


def compile_matcher(version_constraint):
    """
    Compile a function from a version constraint expression which will match a version tuple
    
    Examples:
    
    .. code-block:: python
        
        # Each component may have an exact match, a wildcard, OR one or two operators
        
        # ============ Operator Basics ===========
        
        # Wildcard match is signified by: *
        # Available operators are: >, <, >=, <=
        
        # match 3 exactly 
        
        matcher = compile_matcher('3')
        print(matcher('3'))  # -> True
        print(matcher('7'))  # -> False
        
        # match wildcard
        
        matcher = compile_matcher('*')
        print(matcher(1))  # -> True
        print(matcher(...))  # -> True
        
        # match >= 3
        
        matcher = compile_matcher('>=3')
        print(matcher('7'))  # -> True
        
        # match >= 3 <= 5
        
        matcher = compile_matcher('>=3<=5')
        
        print(matcher('4'))  # -> True
        print(matcher('7'))  # -> False
        
        
        # The following is an error because the first
        # operator is not specified:
        
        compile_matcher('3<=5') # -> VersionFilterSyntaxError
        
        
        # =========== Multiple Version Components =========== 

        # Version components are separated by '.' and whitespace 
        # is insignificant.  You can use as many version components 
        # as you want in your constraint.  
        
        # If you match against a version with more components, the extra 
        # components in it are ignored (wildcarded).
        
        # If you match against a version with less components than your constraint,
        # then the missing components in the version are treated as 0.
        
        # All version components are allowed to use operators
        # and wildcard expressions
        
        
        # ====
        
        # match major version greater than or equal to three
        # match minor version greater than 4
        
        matcher = compile_matcher('>=3<=5 . >=4')
        
        print(matcher('4.5'))  # -> True
        print(matcher('4.3'))  # -> False
        
        
        # ====
        
        # Match all major versions equal to twelve
        
        matcher = compile_matcher('12.*')
        print(matcher('12.0'))  # -> True
        print(matcher('12.1'))  # -> True
        
        
        # This is equivalent to above.
        # If the version you are matching has more components 
        # than your version constraint, then they are ignored.
        
        matcher = compile_matcher('12')
        print(matcher('12.0'))  # -> True
        print(matcher('12.1'))  # -> True
        
        
        # If the version you are matching has less components
        # than your version constraint.  The constraint treats
        # the absent components in the version as being 0
        
        matcher = compile_matcher('12.0.0')
        print(matcher('12'))  # -> True
        print(matcher('12.0'))  # -> True
        
        matcher = compile_matcher('12.0.>5')
        print(matcher('12'))  # -> False
        print(matcher('12.0'))  # -> False
        print(matcher('12.0.6'))  # -> True
        
        
        # ====
        
        # These sorts of expressions will work, though 
        # the usefulness of them is debatable
        
        matcher = compile_matcher('>=12.*.5')
        print(matcher('12.0'))  # -> False
        print(matcher('12.1.5'))  # -> True
        
        matcher = compile_matcher('>=12.*.5.>=3')
        print(matcher('12.1.5.1'))  # -> False
        print(matcher('12.1.5.5'))  # -> True
        print(matcher('13.10.5.5'))  # -> True
        
    
    :param version_constraint: Version constraint string, or tuple/list of version components (they get cast to int)
    :return: A function accepting a version string, or an iterable of version components (they get cast to int)
    """

    version_constraint = _REMOVE_SPACE_REGEX.sub("", version_constraint)
    version_constraint = version_constraint.split('.')
    matcher_functions = []

    for constraint_str in version_constraint:

        constraint = _VERSION_CONSTRAINT_COMPONENT_REGEX.match(constraint_str)
        if not constraint:
            raise VersionFilterSyntaxError(
                'Syntax error in version filter: {filter}'.format(filter=constraint_str)
            )

        c_op_one = constraint.group('op_one')
        c_component = constraint.group('component')
        c_op_two = constraint.group('op_two')
        c_op_two_arg = constraint.group('op_two_arg')

        if c_component == '*':
            if c_op_one or c_op_two:
                raise VersionFilterSyntaxError(
                    'Cannot use operators against wildcard expression.  Offending filter: {filter}'
                        .format(filter=constraint_str)
                )

            matcher_functions.append(lambda in_component: True)
            continue
        else:
            c_component = int(c_component)

        if c_op_two_arg:
            c_op_two_arg = int(c_op_two_arg)

        if c_op_one and c_op_two:
            op_one = _get_operator(c_op_one)
            op_two = _get_operator(c_op_two)

            # curry
            def _create_matcher(constraint_component, constraint_op_two_arg):
                return lambda in_component: op_one(in_component, constraint_component) and op_two(in_component,
                                                                                                  constraint_op_two_arg)

            matcher_functions.append(_create_matcher(c_component, c_op_two_arg))

            continue

        elif c_op_one:
            op = _get_operator(c_op_one)

            # curry
            def _create_matcher(constraint_component):
                return lambda in_component: op(in_component, constraint_component)

            matcher_functions.append(_create_matcher(c_component))

        elif c_op_two:
            raise VersionFilterSyntaxError(
                'Secondary version component operator must be used with a primary version component operator.  '
                'Offending filter: {filter}'.format(filter=constraint_str)
            )
        else:

            # curry
            def _create_matcher(constraint_component):
                return lambda in_component: in_component == constraint_component

            matcher_functions.append(_create_matcher(c_component))

    def _match(version):
        if type(version) is str:
            version = [int(i) for i in _REMOVE_SPACE_REGEX.sub("", version).split('.')]
        else:
            version = [int(i) for i in version]

        len_version = len(version)
        len_matcher_functions = len(matcher_functions)

        if len_version < len_matcher_functions:
            # treat missing components as 0
            version += [0 for i in range(len_matcher_functions - len_version)]

        return functools.reduce(lambda l, r: l and r[0](r[1]), zip(matcher_functions, version), True)

    return _match
