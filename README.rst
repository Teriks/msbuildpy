|docs|

**msbuildpy** is a small python library for locating MSBuild, xbuild and dotnet build binaries.

Works for msbuild/xbuild/dotnet build major versions 12+

**msbuildpy** can be used on Windows and Nix like platforms

It also contains tools to:

 - Directly read the CorFlags from .NET Assemblies/Executables.

 - Determine system architecture and host OS.

 - Find mono VM installations.


Example:

.. code-block:: python

    import msbuildpy
    from msbuildpy.sysinspect import get_mono_vm, is_windows, ARCH64, ARCH32
    from msbuildpy import corflags

    for i in msbuildpy.find_msbuild('msbuild >=12.* | xbuild >=12.* | dotnet build *.*'):
        print(i)

    print('\n')

    print(get_mono_vm())


    print(get_mono_vm(arch=ARCH32))


    print(get_mono_vm(arch=ARCH64))


    print(is_windows())


    test = corflags.read_file(
        'C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\MSBuild\\15.0\\Bin\\MSBuild.exe'
    )

    print('\n')

    print(test.pe_format)
    print(test.is_signed)
    print(test.is_pure_il)
    print(test.processor_architecture)
    print(test.clr_header_major)
    print(test.clr_header_minor)
    print(test.clr_header)

Output:

.. code-block:: bash

    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='64bit', edition='community', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\MSBuild\\15.0\\Bin\\amd64\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='64bit', edition='professional', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Professional\\MSBuild\\15.0\\Bin\\amd64\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='64bit', edition='enterprise', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Enterprise\\MSBuild\\15.0\\Bin\\amd64\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='64bit', edition='standalone', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\BuildTools\\MSBuild\\15.0\\Bin\\amd64\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='32bit', edition='community', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\MSBuild\\15.0\\Bin\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='32bit', edition='professional', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Professional\\MSBuild\\15.0\\Bin\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='32bit', edition='enterprise', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Enterprise\\MSBuild\\15.0\\Bin\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(15, 1, 1012, 6693), arch='32bit', edition='standalone', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\BuildTools\\MSBuild\\15.0\\Bin\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(14, 0, 25123, 0), arch='64bit', edition=None, path='C:\\Program Files (x86)\\MSBuild\\14.0\\bin\\amd64\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(14, 0, 25123, 0), arch='32bit', edition=None, path='C:\\Program Files (x86)\\MSBuild\\14.0\\bin\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(12, 0, 21005, 1), arch='64bit', edition=None, path='C:\\Program Files (x86)\\MSBuild\\12.0\\bin\\amd64\\MSBuild.exe')
    ToolEntry(name='msbuild', version=(12, 0, 21005, 1), arch='32bit', edition=None, path='C:\\Program Files (x86)\\MSBuild\\12.0\\bin\\MSBuild.exe')
    ToolEntry(name='xbuild', version=(14, 0), arch='64bit', edition=None, path='C:\\Program Files\\Mono\\lib\\mono\\xbuild\\14.0\\bin\\xbuild.exe')
    ToolEntry(name='xbuild', version=(14, 0), arch='32bit', edition=None, path='C:\\Program Files (x86)\\Mono\\lib\\mono\\xbuild\\14.0\\bin\\xbuild.exe')
    ToolEntry(name='xbuild', version=(12, 0), arch='64bit', edition=None, path='C:\\Program Files\\Mono\\lib\\mono\\xbuild\\12.0\\bin\\xbuild.exe')
    ToolEntry(name='xbuild', version=(12, 0), arch='32bit', edition=None, path='C:\\Program Files (x86)\\Mono\\lib\\mono\\xbuild\\12.0\\bin\\xbuild.exe')
    ToolEntry(name='dotnet build', version=(15, 1, 1012, 6693), arch='64bit', edition=None, path='C:\\Program Files\\dotnet\\dotnet.exe')


    MonoVm(version=(4, 8, 0), arch='64bit', path='C:\\Program Files\\Mono\\bin\\mono.exe')
    MonoVm(version=(4, 8, 0), arch='32bit', path='C:\\Program Files (x86)\\Mono\\bin\\mono.exe')
    MonoVm(version=(4, 8, 0), arch='64bit', path='C:\\Program Files\\Mono\\bin\\mono.exe')
    True


    PEFormat.PE32
    True
    True
    AssemblyArchitecture.X86
    2
    5
    (2, 5)

.. |docs| image:: https://readthedocs.org/projects/msbuildpy/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: http://msbuildpy.readthedocs.io/en/latest/?badge=latest