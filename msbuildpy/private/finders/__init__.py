import glob
from importlib import import_module
from os.path import dirname, basename, isfile


modules = glob.glob(dirname(__file__) + "/*.py")

__all__ = [basename(f)[:-3] for f in modules if isfile(f)]

for i in ('.'+x for x in __all__):
    import_module(i, 'msbuildpy.private.finders')
