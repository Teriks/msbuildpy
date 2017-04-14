Small python library for locating MSBuild, xbuild and dotnet build binaries.


Works for msbuild/xbuild/dotnet build major versions 12+

```python

import msbuildpy
from msbuildpy.inspect import get_mono_vm, ARCH64, ARCH32
from msbuildpy.corflags import CorFlagsReader

for i in msbuildpy.find_msbuild('msbuild >=12.* | xbuild >=12.*'):
    print(i)


print(get_mono_vm())


print(get_mono_vm(arch=ARCH32))


print(get_mono_vm(arch=ARCH64))


test = CorFlagsReader.read_file('C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\MSBuild\\15.0\\Bin\\MSBuild.exe')
print(test.processor_architecture)

```

Output:

```

ToolEntry(name='msbuild', version=(15, 0), arch='32bit', path='C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\MSBuild\\15.0\\Bin\\MSBuild.exe')
ToolEntry(name='msbuild', version=(14, 0), arch='64bit', path='C:\\Program Files (x86)\\MSBuild\\14.0\\bin\\amd64\\MSBuild.exe')
ToolEntry(name='msbuild', version=(14, 0), arch='32bit', path='C:\\Program Files (x86)\\MSBuild\\14.0\\bin\\MSBuild.exe')
ToolEntry(name='msbuild', version=(12, 0), arch='64bit', path='C:\\Program Files (x86)\\MSBuild\\12.0\\bin\\amd64\\MSBuild.exe')
ToolEntry(name='msbuild', version=(12, 0), arch='32bit', path='C:\\Program Files (x86)\\MSBuild\\12.0\\bin\\MSBuild.exe')
ToolEntry(name='xbuild', version=(14, 0), arch='64bit', path='C:\\Program Files\\Mono\\lib\\mono\\xbuild\\14.0\\bin\\xbuild.exe')
ToolEntry(name='xbuild', version=(14, 0), arch='32bit', path='C:\\Program Files (x86)\\Mono\\lib\\mono\\xbuild\\14.0\\bin\\xbuild.exe')
ToolEntry(name='xbuild', version=(12, 0), arch='64bit', path='C:\\Program Files\\Mono\\lib\\mono\\xbuild\\12.0\\bin\\xbuild.exe')
ToolEntry(name='xbuild', version=(12, 0), arch='32bit', path='C:\\Program Files (x86)\\Mono\\lib\\mono\\xbuild\\12.0\\bin\\xbuild.exe')
MonoVersion(version=(4, 8, 0), arch='64bit', path='C:\\Program Files\\Mono\\bin\\mono.exe')
MonoVersion(version=(4, 8, 0), arch='32bit', path='C:\\Program Files (x86)\\Mono\\bin\\mono.exe')
MonoVersion(version=(4, 8, 0), arch='64bit', path='C:\\Program Files\\Mono\\bin\\mono.exe')
AssemblyArchitecture.X86

```


Work in progress