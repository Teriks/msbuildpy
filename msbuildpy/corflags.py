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
Contains tools for reading CorFlags from .NET assemblies/executables.
"""

from enum import Enum as Enum
from struct import unpack

from collections import namedtuple


class PEFormat(Enum):
    """
    Represents a Portable Executable File's format.
    """

    PE32 = 0x10b
    PE32Plus = 0x20b


class AssemblyArchitecture(Enum):
    """
    Represents a .NET assembly's architecture.
    
    :var MSIL: Built for AnyCPU
    :var X86: Built for x86 (32bit)
    :var X64: Built for x64 (64bit)
    """

    MSIL = 0
    X86 = 1
    X64 = 2


class CorFlagsBits:
    """
    Represents PE file's CorFlags section bitfield value.
    """

    F32BitsRequired = 2
    ILOnly = 1
    StrongNameSigned = 8
    TrackDebugData = 0x10000

    @property
    def value(self):
        """
        Get the integer value, alternatively you can use int() on the flags object.
        
        :return: Integer value of the flags. 
        """
        return self._value

    def __int__(self):
        return self._value

    def __or__(self, other):
        if type(other) is int:
            return self._value | other
        return self._value | other._value

    def __and__(self, other):
        if type(other) is int:
            return self._value & other
        return self._value & other._value

    def __init__(self, value):
        self._value = value

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return str(self._value)


class CorFlags:
    """
    Holds/interprets CorFlags information read from a .NET assembly/executable.
    
    Returned by :py:func:`msbuildpy.corflags.read` and :py:func:`msbuildpy.corflags.read_file`.
    """

    def __init__(self, clr_header_major, clr_header_minor, corflags, pe_format):
        self._clr_header_major = clr_header_major
        self._clr_header_minor = clr_header_minor
        self._corflags = corflags
        self._pe_format = pe_format

    @property
    def is_signed(self):
        """
        Check if the assembly is strong name signed.
        
        :return: bool
        """

        return (self._corflags & CorFlagsBits.StrongNameSigned) == CorFlagsBits.StrongNameSigned

    @property
    def is_pure_il(self):
        """
        Check if the assembly is Pure IL.
        
        :return: bool
        """

        return (self._corflags & CorFlagsBits.ILOnly) == CorFlagsBits.ILOnly

    @property
    def processor_architecture(self):
        """
        Check the processor architecture the assembly was compiled for.
        
        Returns an enum value of :py:class:`msbuildpy.corflags.AssemblyArchitecture`
        
        :return: :py:class:`msbuildpy.corflags.AssemblyArchitecture`
        """

        if self._pe_format == PEFormat.PE32Plus:
            return AssemblyArchitecture.X64
        if (self._corflags & CorFlagsBits.F32BitsRequired) != 0 or not self.is_pure_il:
            return AssemblyArchitecture.X86
        return AssemblyArchitecture.MSIL

    @property
    def clr_header_major(self):
        """
        Get the major version component of the CLR Header.
        
        :return: int
        """

        return self._clr_header_major

    @property
    def clr_header_minor(self):
        """
        Get the minor version component of the CLR Header.
        
        :return: int
        """

        return self._clr_header_minor

    @property
    def clr_header(self):
        """
        Get a (major, minor) version tuple of the CLR Header.
        
        :return: tuple(major, minor)
        """

        return (self._clr_header_major, self._clr_header_minor)

    @property
    def corflags(self):
        """
        Get a :py:class:`msbuildpy.corflags.CorFlagsBits` object representing the CorFlags PE section bitfield.
        
        :return: :py:class:`msbuildpy.corflags.CorFlagsBits`
        """

        return self._corflags

    @property
    def pe_format(self):
        """
        Return the format of the PE (Portable Executable) file.
        
        :return: :py:class:`msbuildpy.corflags.PEFormat`
        """

        return self._pe_format


_Section = namedtuple('Section', ['virtual_size', 'virtual_address', 'pointer'])


def _resolve_rva(sections, rva):
    for section in sections:
        if section.virtual_address <= rva < section.virtual_address + section.virtual_size:
            return rva - section.virtual_address + section.pointer
    return 0


def read(stream):
    """
    Read :py:class:`msbuildpy.corflags.CorFlags` from a .NET assembly in a file stream.
    
    **None** is returned if the PE file is invalid.
    
    :param stream: A file stream that supports random access with **seek**
    
    :return: :py:class:`msbuildpy.corflags.CorFlags` or **None**
    """

    stream.seek(0, 2)
    length = stream.tell()
    stream.seek(0)

    if length < 0x40:
        return None

    stream.seek(0x3c)
    # read UInt32 little-endian
    pe_header_ptr = unpack('<I', stream.read(4))[0]
    if pe_header_ptr == 0:
        pe_header_ptr = 0x80

    if pe_header_ptr > length - 256:
        return None

    stream.seek(pe_header_ptr)
    # read UInt32 little-endian
    pe_signature = unpack('<I', stream.read(4))[0]
    if pe_signature != 0x00004550:
        return None

    # read UInt16 little-endian
    machine = unpack('<H', stream.read(2))[0]
    number_of_sections = unpack('<H', stream.read(2))[0]

    # read UInt32 little-endian
    timestamp = unpack('<I', stream.read(4))[0]
    symbol_table_ptr = unpack('<I', stream.read(4))[0]
    number_of_symbols = unpack('<I', stream.read(4))[0]

    # read UInt16 little-endian
    optional_header_size = unpack('<H', stream.read(2))[0]
    characteristics = unpack('<H', stream.read(2))[0]

    # read UInt16 little-endian
    pe_format = PEFormat(unpack('<H', stream.read(2))[0])

    if pe_format != PEFormat.PE32 and pe_format != PEFormat.PE32Plus:
        return None

    stream.seek(pe_header_ptr + 232 if pe_format == PEFormat.PE32 else 248)

    # read UInt32 little-endian
    cli_header_rva = unpack('<I', stream.read(4))[0]

    if cli_header_rva == 0:
        return None

    section_table_ptr = pe_header_ptr + 24 + optional_header_size

    sections = []
    for i in range(number_of_sections):
        stream.seek(section_table_ptr + i * 40 + 8)

        virtual_size = unpack('<I', stream.read(4))[0]
        virtual_address = unpack('<I', stream.read(4))[0]
        stream.read(4)
        pointer = unpack('<I', stream.read(4))[0]

        sections.append(_Section(virtual_size, virtual_address, pointer))

    cli_header_ptr = _resolve_rva(sections, cli_header_rva)
    if cli_header_ptr == 0:
        return None

    stream.seek(cli_header_ptr + 4)

    # read UInt16 little-endian
    clr_header_major = unpack('<H', stream.read(2))[0]
    clr_header_minor = unpack('<H', stream.read(2))[0]

    # read UInt32 little-endian
    metadata_rva = unpack('<I', stream.read(4))[0]
    metadata_size = unpack('<I', stream.read(4))[0]

    corflags = CorFlagsBits(unpack('<I', stream.read(4))[0])

    return CorFlags(clr_header_major, clr_header_minor, corflags, pe_format)


def read_file(filename):
    """
    Read :py:class:`msbuildpy.corflags.CorFlags` from a .NET assembly file path.
    
    **None** is returned if the PE file is invalid.
    
    :param filename: A file path to a .NET assembly/executable.
    
    :return: :py:class:`msbuildpy.corflags.CorFlags` or **None**
    """

    with open(filename, 'rb') as f:
        return read(f)
