"""Unit tests for common definitions."""

from pytest import CaptureFixture
from collections import OrderedDict
from osmg.core.common import (
    EPSILON,
    ALPHA,
    methods,
    print_methods,
    print_dir,
    previous_element,
)


class TestConstants:
    """Tests for constants defined in the module."""

    def test_constants_values(self):
        """
        Test the values of constants.

        Ensures constants have the expected values.
        """
        assert EPSILON == 1.00e-6, 'EPSILON has an incorrect value'
        assert ALPHA == 1.00e8, 'ALPHA has an incorrect value'


class TestMethodsFunction:
    """Tests for the `methods` function."""

    def test_methods_extraction(self):
        """
        Test that `methods` correctly extracts callable methods.

        Verifies that only non-dunder methods are returned.
        """

        class TestClass:
            def method_1(self):
                pass

            def method_2(self):
                pass

        obj = TestClass()
        result = methods(obj)
        expected = ['method_1', 'method_2']
        assert result == expected, f'Expected {expected}, but got {result}'


class TestPrintFunctions:
    """Tests for `print_methods` and `print_dir` functions."""

    def test_print_methods(self, capsys: CaptureFixture[str]) -> None:
        """
        Test `print_methods` for correct output.

        Verifies that the correct methods are printed.
        """

        class TestClass:
            def method_1(self):
                pass

            def method_2(self):
                pass

        obj = TestClass()
        print_methods(obj)
        captured = capsys.readouterr()
        assert "['method_1', 'method_2']" in captured.out, 'Output did not match'

    def test_print_dir(self, capsys: CaptureFixture[str]) -> None:
        """
        Test `print_dir` for correct output.

        Verifies that `dir` output is printed.
        """

        class TestClass:
            def method_1(self):
                pass

        obj = TestClass()
        print_dir(obj)
        captured = capsys.readouterr()
        assert (
            '__class__' in captured.out
        ), 'Output did not include expected attributes'


class TestPreviousElementFunction:
    """Tests for the `previous_element` function."""

    def test_previous_element_found(self) -> None:
        """
        Test `previous_element` for finding the correct previous element.

        Verifies correct value is returned for a valid key.
        """
        dct = OrderedDict([(1, 'a'), (2, 'b'), (3, 'c')])
        assert (
            previous_element(dct, 2) == 'a'
        ), 'Incorrect previous element for key 2'
        assert (
            previous_element(dct, 3) == 'b'
        ), 'Incorrect previous element for key 3'

    def test_previous_element_not_found(self) -> None:
        """
        Test `previous_element` when no previous element exists.

        Verifies `None` is returned for the first element or non-existent keys.
        """
        dct = OrderedDict([(1, 'a'), (2, 'b'), (3, 'c')])
        assert previous_element(dct, 1) is None, 'Expected None for the first key'
        assert (
            previous_element(dct, 4) is None
        ), 'Expected None for a non-existent key'
