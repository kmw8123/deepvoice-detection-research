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
    for e in source["copied"]:
        if sha(inside(e["archive_path"])) != e["sha256"]:
            errors.append("Original-copy hash mismatch: " + e["archive_path"])
    for e in source["annotated"]:
        original, annotated = inside(e["original"]), inside(e["annotated"])
        a = ast.dump(ast.parse(original.read_text(encoding="utf-8")), include_attributes=False)
        b = ast.dump(ast.parse(annotated.read_text(encoding="utf-8")), include_attributes=False)
        if a != b or sha(annotated) != e["annotated_sha256"]:
            errors.append("Annotation parity/hash mismatch: " + e["annotated"])

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
        "python_files_parsed": python_count,
        "local_document_links_checked": links_checked,
        "registered_C_ids": inventory["registered_C_ids"],
        "directory_count": inventory["directory_count"],
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
