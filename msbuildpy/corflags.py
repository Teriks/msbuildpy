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


from struct import unpack
from collections import namedtuple
from enum import Enum as Enum


class PEFormat(Enum):
    PE32 = 0x10b
    PE32Plus = 0x20b


class AssemblyArchitecture(Enum):
    MSIL = 0
    X86 = 1
    X64 = 2


class CorFlags:
    F32BitsRequired = 2
    ILOnly = 1
    StrongNameSigned = 8
    TrackDebugData = 0x10000

    @property
    def value(self):
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


class CorFlagsReader:
    Section = namedtuple('Section', ['virtual_size', 'virtual_address', 'pointer'])

    def __init__(self, major_runtime_version, minor_runtime_version, corflags, pe_format):
        self._major_runtime_version = major_runtime_version
        self._minor_runtime_version = minor_runtime_version
        self._corflags = corflags
        self._pe_format = pe_format

    @staticmethod
    def read_file(filename):
        with open(filename, 'rb') as f:
            return CorFlagsReader.read(f)

    @staticmethod
    def read(stream):
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
        cli_header_rva = number_of_symbols = unpack('<I', stream.read(4))[0]
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

            sections.append(CorFlagsReader.Section(virtual_size, virtual_address, pointer))

        cli_header_ptr = CorFlagsReader._resolve_rva(sections, cli_header_rva)
        if cli_header_ptr == 0:
            return None

        stream.seek(cli_header_ptr + 4)
        # read UInt16 little-endian
        major_runtime_version = unpack('<H', stream.read(2))[0]
        minor_runtime_version = unpack('<H', stream.read(2))[0]
        # read UInt32 little-endian
        metadata_rva = unpack('<I', stream.read(4))[0]
        metadata_size = unpack('<I', stream.read(4))[0]
        corflags = CorFlags(unpack('<I', stream.read(4))[0])

        return CorFlagsReader(major_runtime_version, minor_runtime_version, corflags, pe_format)

    @staticmethod
    def _resolve_rva(sections, rva):
        for section in sections:
            if rva >= section.virtual_address and rva < section.virtual_address + section.virtual_size:
                return rva - section.virtual_address + section.pointer

        return 0

    @property
    def is_signed(self):
        return (self._corflags & CorFlags.StrongNameSigned) == CorFlags.StrongNameSigned

    @property
    def is_pure_il(self):
        return (self._corflags & CorFlags.ILOnly) == CorFlags.ILOnly

    @property
    def processor_architecture(self):
        if self._pe_format == PEFormat.PE32Plus:
            return AssemblyArchitecture.X64
        if (self._corflags & CorFlags.F32BitsRequired) != 0 or not self.is_pure_il:
            return AssemblyArchitecture.X86
        return AssemblyArchitecture.MSIL

    @property
    def major_runtime_version(self):
        return self._major_runtime_version

    @property
    def minor_runtime_version(self):
        return self._minor_runtime_version

    @property
    def corflags(self):
        return self._corflags

    @property
    def pe_format(self):
        return self._pe_format
