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


from os.path import basename as path_basename

from os import environ as os_environ

from msbuildpy.searcher import add_default_finder
from msbuildpy.sysinspect import ARCH32
from . import finder_util
from importlib import import_module


def _env_msbuild_paths():
    values = []

    msbuild = os_environ.get('MSBUILD_PATH', None)
    xbuild = os_environ.get('XBUILD_PATH', None)

    if msbuild:
        if path_basename(msbuild).lower() == 'dotnet':
            values += finder_util.parse_dotnetcli_msbuild_ver_output(msbuild, ARCH32)
        else:
            values += finder_util.parse_msbuild_ver_output(msbuild, ARCH32)

    if xbuild:
        values += finder_util.parse_xbuild_ver_output(xbuild, ARCH32)

    return values


add_default_finder(_env_msbuild_paths)


import_module('msbuildpy.private.finders')

