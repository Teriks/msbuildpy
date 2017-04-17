from setuptools import setup, find_packages
import re

version = ''
with open('msbuildpy/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

readme = ''
with open('README.rst') as f:
    readme = f.read()


setup(name='msbuildpy',
      author='Teriks',
      url='https://github.com/Teriks/msbuildpy',
      version=version,
      packages=find_packages(exclude=["docs", "tests"]),
      license='BSD 3-Clause',
      description='A small python library for locating MSBuild, xbuild and dotnet build binaries.',
      long_description=readme,
      include_package_data=True,
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: BSD 3-Clause License',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Utilities',
      ]
      )
