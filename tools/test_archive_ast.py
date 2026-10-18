"""Regression tests for static editorial parity; no model imports or execution.

Run with: python -B -m unittest discover -s tools -p test_archive_ast.py
The verifier is loaded through runpy, which does not cache this local script.
"""
import runpy
import unittest
from pathlib import Path


compare_python_sources = runpy.run_path(
    str(Path(__file__).with_name("verify_archive.py")),
    run_name="_archive_verifier_for_tests",
)["compare_python_sources"]


class EditorialAstParityTests(unittest.TestCase):
    def assert_comparison(self, original, annotated, *, full, editorial):
        observed = compare_python_sources(original, annotated)
        self.assertIs(observed["ast_identical"], full)
        self.assertIs(
            observed["executable_ast_identical_excluding_docstrings"], editorial
        )

    def test_comment_edits_preserve_full_ast(self):
        self.assert_comparison(
            "value = 7\n", "# Explain the fixed value.\nvalue = 7\n",
            full=True, editorial=True,
        )

    def test_leading_docstrings_in_all_supported_scopes(self):
        original = '''"""Original module description."""
class Detector:
    """Original class description."""
    def predict(self):
        """Original function description."""
        return "same runtime value"
    async def fetch(self):
        """Original async function description."""
        return 7
'''
        self.assert_comparison(
            original, original.replace("Original", "Expanded editorial"),
            full=False, editorial=True,
        )

    def test_added_or_removed_docstrings_are_editorial_only(self):
        without = "def predict():\n    return 7\n"
        with_doc = 'def predict():\n    """Describe the method."""\n    return 7\n'
        self.assert_comparison(without, with_doc, full=False, editorial=True)
        self.assert_comparison(with_doc, without, full=False, editorial=True)

    def test_numeric_constants_remain_compared(self):
        self.assert_comparison("value = 7\n", "value = 8\n", full=False, editorial=False)

    def test_runtime_exception_messages_remain_compared(self):
        self.assert_comparison(
            'raise ValueError("original")\n', 'raise ValueError("changed")\n',
            full=False, editorial=False,
        )

    def test_assigned_strings_remain_compared(self):
        self.assert_comparison(
            'path = "original"\n', 'path = "changed"\n',
            full=False, editorial=False,
        )

    def test_returned_strings_remain_compared(self):
        self.assert_comparison(
            'def label():\n    return "original"\n',
            'def label():\n    return "changed"\n',
            full=False, editorial=False,
        )

    def test_second_string_expression_after_docstring_remains_compared(self):
        self.assert_comparison(
            '"""Same module doc."""\n"original extra expression"\n',
            '"""Same module doc."""\n"changed extra expression"\n',
            full=False, editorial=False,
        )

    def test_later_function_string_expression_remains_compared(self):
        self.assert_comparison(
            'def run():\n    value = 7\n    "original"\n',
            'def run():\n    value = 7\n    "changed"\n',
            full=False, editorial=False,
        )

    def test_added_non_docstring_expression_remains_compared(self):
        self.assert_comparison(
            '"""Same module doc."""\nvalue = 7\n',
            '"""Same module doc."""\n"additional expression"\nvalue = 7\n',
            full=False, editorial=False,
        )

    def test_strings_inside_other_statement_bodies_are_not_docstrings(self):
        self.assert_comparison(
            'if enabled:\n    "original"\n',
            'if enabled:\n    "changed"\n',
            full=False, editorial=False,
        )

    def test_leading_bytes_and_formatted_strings_are_not_docstrings(self):
        for prefix in ("b", "f"):
            with self.subTest(prefix=prefix):
                self.assert_comparison(
                    f'{prefix}"original"\n', f'{prefix}"changed"\n',
                    full=False, editorial=False,
                )

    def test_property_docstring_differs_from_property_runtime_value(self):
        original = '''class Detector:
    @property
    def label(self):
        """Original property documentation."""
        return "original runtime label"
'''
        self.assert_comparison(
            original, original.replace("Original property", "Expanded property"),
            full=False, editorial=True,
        )
        self.assert_comparison(
            original, original.replace("original runtime", "changed runtime"),
            full=False, editorial=False,
        )

    def test_dunder_doc_assignment_is_an_ordinary_assignment(self):
        self.assert_comparison(
            '__doc__ = "original"\n', '__doc__ = "changed"\n',
            full=False, editorial=False,
        )


if __name__ == "__main__":
    unittest.main()
