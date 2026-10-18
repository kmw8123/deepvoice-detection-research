"""Verify archive integrity WITHOUT importing model code or running ML. Python 3.11+."""
import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PYTHON_MIRRORS = 10
EXPECTED_ORIGINAL_COPIES = 22


class _RemoveLeadingDocstrings(ast.NodeTransformer):
    """Remove only Python's leading docstring statement in eligible scopes.

    Assigned strings, return values, exception messages, and later standalone
    string expressions remain in the AST. This is an editorial comparison,
    not a claim that changing __doc__ is invisible to Python introspection.
    """

    def _visit_scope(self, node):
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body = node.body[1:]
        return self.generic_visit(node)

    visit_Module = _visit_scope
    visit_ClassDef = _visit_scope
    visit_FunctionDef = _visit_scope
    visit_AsyncFunctionDef = _visit_scope


def compare_python_sources(original_text, annotated_text):
    """Return separate full-AST and documented editorial-parity booleans.

    I parse source text only. Neither source is imported or executed. Comments
    and location attributes are absent from the comparison; only the second
    comparison additionally removes actual leading docstrings.
    """
    original = ast.parse(original_text)
    annotated = ast.parse(annotated_text)
    full_equal = ast.dump(original, include_attributes=False) == ast.dump(
        annotated, include_attributes=False
    )
    executable_equal = ast.dump(
        _RemoveLeadingDocstrings().visit(original), include_attributes=False
    ) == ast.dump(
        _RemoveLeadingDocstrings().visit(annotated), include_attributes=False
    )
    return {
        "ast_identical": full_equal,
        "executable_ast_identical_excluding_docstrings": executable_equal,
    }


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inside(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Path escapes archive")
    return path


def verify():
    errors = []
    manifest = json.loads((ROOT / "provenance/FILE_MANIFEST.json").read_text(encoding="utf-8"))
    expected = {e["path"] for e in manifest["files"]}
    extras_allowed = {"provenance/FILE_MANIFEST.json", "provenance/VERIFICATION.json"}
    files = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.relative_to(ROOT).parts]
    actual = {p.relative_to(ROOT).as_posix() for p in files}
    for extra in sorted(actual - expected - extras_allowed):
        errors.append("Unlisted file: " + extra)
    for e in manifest["files"]:
        path = inside(e["path"])
        if not path.is_file() or path.stat().st_size != e["bytes"] or sha(path) != e["sha256"]:
            errors.append("Manifest mismatch: " + e["path"])

    source = json.loads((ROOT / "provenance/source_manifest.json").read_text(encoding="utf-8"))
    if len(source["copied"]) != EXPECTED_ORIGINAL_COPIES:
        errors.append("Expected exactly 22 original byte copies")
    for e in source["copied"]:
        path = inside(e["archive_path"])
        if not path.is_file() or sha(path) != e["sha256"]:
            errors.append("Original-copy hash mismatch: " + e["archive_path"])

    original_python = {p.relative_to(ROOT / "src").as_posix() for p in (ROOT / "src").rglob("*.py") if p.is_file()}
    annotated_python = {p.relative_to(ROOT / "annotated").as_posix() for p in (ROOT / "annotated").rglob("*.py") if p.is_file()}
    if len(original_python) != EXPECTED_PYTHON_MIRRORS:
        errors.append("Expected exactly 10 original Python files")
    if annotated_python != original_python:
        errors.append("Annotated Python paths must exactly mirror all original Python paths")
    expected_pairs = {(f"src/{name}", f"annotated/{name}") for name in original_python}
    listed_pairs = [(e["original"], e["annotated"]) for e in source["annotated"]]
    if len(listed_pairs) != len(expected_pairs) or set(listed_pairs) != expected_pairs:
        errors.append("Annotation manifest must list each original/mirror pair exactly once")

    full_ast_equal_count = 0
    executable_ast_equal_count = 0
    for e in source["annotated"]:
        original, annotated = inside(e["original"]), inside(e["annotated"])
        if not original.is_file() or not annotated.is_file():
            errors.append("Missing annotation pair: " + e["annotated"])
            continue
        comparison = compare_python_sources(
            original.read_text(encoding="utf-8"), annotated.read_text(encoding="utf-8")
        )
        full_ast_equal_count += int(comparison["ast_identical"])
        executable_ast_equal_count += int(comparison["executable_ast_identical_excluding_docstrings"])
        if not comparison["executable_ast_identical_excluding_docstrings"]:
            errors.append("Non-docstring AST mismatch: " + e["annotated"])
        for key, value in comparison.items():
            if type(e.get(key)) is not bool or e[key] != value:
                errors.append("Incorrect annotation boolean " + key + ": " + e["annotated"])
        if sha(original) != e["original_sha256"] or sha(annotated) != e["annotated_sha256"]:
            errors.append("Annotation source/mirror hash mismatch: " + e["annotated"])

    forbidden = {".zip", ".wav", ".mp3", ".flac", ".ogg", ".opus", ".m4a", ".bin", ".pt", ".pth", ".th", ".npz", ".npy", ".safetensors", ".whl", ".pem", ".key", ".csv"}
    suspicious = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{24,}|hf_[A-Za-z0-9]{24,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|[A-Za-z]:[/\\]Users[/\\])")
    python_count = 0
    links_checked = 0
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if path.is_symlink() or path.suffix.lower() in forbidden or path.stat().st_size > 2_000_000 or path.name.startswith(".env"):
            errors.append("Disallowed asset: " + rel)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append("Non-UTF8/binary file: " + rel)
            continue
        if "\ufffd" in text or "\x00" in text:
            errors.append("Invalid text marker: " + rel)
        if re.search(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]", text):
            errors.append("Untranslated Korean text: " + rel)
        if rel in {"README.md", "EXPERIMENTS.md", "MODEL_CARD.md", "REPRODUCIBILITY.md", "THIRD_PARTY_NOTICES.md", "LICENSE_POLICY.md"}:
            if re.search(r"\b(?:the user (?:reported|provided|requested|said|instructed)|user-reported|provided by the user)\b", text, re.I):
                errors.append("Assistant-perspective attribution in authored prose: " + rel)
        if suspicious.search(text):
            errors.append("Credential or personal-path pattern: " + rel)
        if path.suffix == ".py":
            ast.parse(text, filename=rel)
            python_count += 1
        # Original notices retain historical package-relative references unchanged.
        if path.suffix == ".md" and not rel.startswith("notices/"):
            for target in re.findall(r"\]\(([^\s)]+)\)", text):
                if urlsplit(target).scheme or target.startswith("#"):
                    continue
                link = path.parent / unquote(target.split("#", 1)[0])
                links_checked += 1
                if not link.exists() or not link.resolve().is_relative_to(ROOT):
                    errors.append("Broken local link in " + rel + ": " + target)

    inventory = json.loads((ROOT / "experiment_inventory.json").read_text(encoding="utf-8"))
    if inventory["registered_C_ids"] != len(inventory["items"]):
        errors.append("Inventory count mismatch")
    result = {
        "status": "PASS_STATIC_ARCHIVE" if not errors else "FAIL",
        "scope": "Integrity, syntax/AST and content-hygiene checks only. No model imports, training, inference, metric recomputation, uploads or large original asset rehashes.",
        "manifest_files": len(manifest["files"]),
        "original_byte_copies": len(source["copied"]),
        "annotated_ast_pairs": len(source["annotated"]),
        "full_ast_identical_pairs": full_ast_equal_count,
        "executable_ast_identical_excluding_docstrings_pairs": executable_ast_equal_count,
        "annotation_comparison_policy": "Only first-statement string docstrings in modules, classes, functions and async functions are removed for editorial parity. All other AST nodes, including runtime strings, remain compared. Docstrings and __doc__ introspection may differ; full AST identity is reported separately.",
        "python_files_parsed": python_count,
        "local_document_links_checked": links_checked,
        "registered_C_ids": inventory["registered_C_ids"],
        "directory_count": inventory["directory_count"],
        "editorial_checks": "No untranslated Korean text; authored prose excludes assistant-perspective user attribution. Original third-party notices are preserved.",
        "secret_scan_limit": "Pattern scan plus human review, not a proof that every possible secret is absent.",
        "errors": errors,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true", help="Write the small static verification report; never changes model files.")
    args = parser.parse_args()
    result = verify()
    if args.write_report:
        (ROOT / "provenance/VERIFICATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "PASS_STATIC_ARCHIVE" else 1


if __name__ == "__main__":
    sys.exit(main())
