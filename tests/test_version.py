import unittest
from msbuildpy.version import compile_matcher, VersionFilterSyntaxError


class TestStringMethods(unittest.TestCase):
    def test_compile_matcher(self):
        # These sorts of expression will work, though
        # the usefulness of them is debatable

        # match major version greater than or equal to three
        # match minor version greater than 4

        matcher = compile_matcher('>=3<=5 . >=4')

        self.assertTrue(matcher('4.5'))  # -> True
        self.assertFalse(matcher('4.3'))  # -> False

        # ====

        # Match all major versions equal to twelve

        matcher = compile_matcher('12.*')
        self.assertTrue(matcher('12.0'))  # -> True
        self.assertTrue(matcher('12.1'))  # -> True

        # This is equivalent to above.
        # If the version you are matching has more components
        # than your version constraint, then they are ignored.

        matcher = compile_matcher('12')
        self.assertTrue(matcher('12.0'))  # -> True
        self.assertTrue(matcher('12.1'))  # -> True

        # If the version you are matching has less components
        # than your version constraint.  The constraint treats
        # the absent components in the version as being 0

        matcher = compile_matcher('12.0.0')
        self.assertTrue(matcher('12'))  # -> True
        self.assertTrue(matcher('12.0'))  # -> True

        matcher = compile_matcher('12.0.>5')
        self.assertFalse(matcher('12'))  # -> False
        self.assertFalse(matcher('12.0'))  # -> False
        self.assertTrue(matcher('12.0.6'))  # -> True

        # ====

        # These sorts of expressions will work, though
        # the usefulness of them is debatable

        matcher = compile_matcher('>=12.*.5')
        self.assertFalse(matcher('12.0'))  # -> False
        self.assertTrue(matcher('12.1.5'))  # -> True

        matcher = compile_matcher('>=12.*.5.>=3')
        self.assertFalse(matcher('12.1.5.1'))  # -> False
        self.assertTrue(matcher('12.1.5.5'))  # -> True
        self.assertTrue(matcher('13.10.5.5'))  # -> True

        # Do not allow the secondary operator against a version
        # component to be used alone.

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('6>=6.*')

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('*.0<8')

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('0.0.0<9')

        # Do not allow operators to be used against wildcards.

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('>=*')

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('>=*<=4')

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('5.>*')

        with self.assertRaises(VersionFilterSyntaxError):
            compile_matcher('5.>*<7')