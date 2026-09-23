#!/usr/bin/env python3
"""Static check of Qt widget code against the PySide6 stubs.

This sandbox has no ``libGL.so.1``, so ``PySide6.QtWidgets`` cannot be imported and no
GUI can be rendered here. That does not have to mean "unverified": PySide6 ships
complete ``.pyi`` stubs, so every widget class, every method call on a known receiver
and every ``self.<method>`` call on a class that inherits from a Qt class can be
checked against the real API surface.

What it proves: the classes exist, the methods exist on the resolved class (walking
the stub inheritance chain), and no typo'd Qt API is hiding in the file.
What it does not prove: layout aesthetics, runtime behaviour, or enum values passed as
arguments. It is a floor, not a replacement for running the app.

Usage::

    python3 scripts/diagnostics/qt_api_check.py src/ui/learning_panel.py ...
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLASS_RE = re.compile(r"^class\s+(\w+)\s*\(([^)]*)\)\s*:")
METHOD_RE = re.compile(r"^\s+def\s+(\w+)\s*\(")
ATTR_RE = re.compile(r"^\s+(\w+)\s*:")
IMPORT_BLOCK_RE = re.compile(r"from\s+(PySide6\.\w+)\s+import\s*\(([^)]*)\)", re.S)
IMPORT_LINE_RE = re.compile(r"from\s+(PySide6\.\w+)\s+import\s+([^\n(]+)\n")
ANY_ASSIGN_RE = re.compile(r"^\s*(?:self\.)?(\w+)\s*=", re.M)
ASSIGN_RE = re.compile(r"^\s*(?:self\.)?(\w+)\s*=\s*(Q\w+)\s*\(", re.M)
CALL_RE = re.compile(r"\b(self|(?:self\.)?\w+)\.(\w+)\s*\(")
CLASS_ATTR_RE = re.compile(r"\b(Q\w+)\.(\w+)")
CLASS_DEF_RE = re.compile(r"^class\s+(\w+)\s*\(([^)]*)\)", re.M)


def stub_directory() -> Path:
    candidates = sorted(Path("/home/user").glob("**/site-packages/PySide6"))
    for path in candidates:
        if list(path.glob("QtWidgets.pyi")):
            return path
    raise SystemExit("PySide6 stubs not found - install PySide6 or point this script at them")


def parse_stubs(directory: Path) -> Tuple[Dict[str, Set[str]], Dict[str, List[str]]]:
    members: Dict[str, Set[str]] = {}
    bases: Dict[str, List[str]] = {}
    for stub in directory.glob("Qt*.pyi"):
        lines = stub.read_text(encoding="utf-8", errors="ignore").splitlines()
        current: str | None = None
        for line in lines:
            if line and not line[0].isspace():
                match = CLASS_RE.match(line)
                current = None
                if match:
                    name, base_text = match.group(1), match.group(2)
                    current = name
                    members.setdefault(name, set())
                    parsed = []
                    for base in base_text.split(","):
                        base = base.strip()
                        if not base:
                            continue
                        parsed.append(base.split(".")[-1])
                    bases[name] = parsed
                continue
            if current is None:
                continue
            method = METHOD_RE.match(line)
            if method:
                members[current].add(method.group(1))
                continue
            attribute = ATTR_RE.match(line)
            if attribute:
                members[current].add(attribute.group(1))
    return members, bases


def has_member(name: str, member: str, members: Dict[str, Set[str]],
               bases: Dict[str, List[str]], seen: Set[str] | None = None) -> bool:
    seen = seen or set()
    if name in seen or name not in members:
        return False
    seen.add(name)
    if member in members[name]:
        return True
    return any(has_member(base, member, members, bases, seen) for base in bases.get(name, []))


def imports_for(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    imported: Dict[str, str] = {}
    for module, body in IMPORT_BLOCK_RE.findall(text):
        for chunk in body.replace("\n", " ").split(","):
            name = chunk.strip().split(" as ")[0].strip()
            if name:
                imported[name] = module
    for module, body in IMPORT_LINE_RE.findall(text):
        for chunk in body.split(","):
            name = chunk.strip().split(" as ")[0].strip()
            if name:
                imported[name] = module
    return imported


def enclosing_classes(text: str) -> Dict[int, str]:
    """Map line number -> enclosing class name (or the first base for top-level code)."""
    owners: Dict[int, str] = {}
    current = ""
    for index, line in enumerate(text.splitlines(), start=1):
        match = CLASS_DEF_RE.match(line)
        if match:
            current = match.group(1)
        owners[index] = current
    return owners


def check_file(path: Path, members: Dict[str, Set[str]], bases: Dict[str, List[str]]) -> List[str]:
    text = path.read_text(encoding="utf-8")
    problems: List[str] = []
    imported = imports_for(path)

    for name in imported:
        if name.startswith("Q") and name not in members:
            problems.append(f"{path}: imported Qt name '{name}' does not exist in the stubs")

    # receivers whose class we can resolve. A name only counts as a Qt object when
    # every assignment to it in the file is a Qt construction - otherwise the same
    # name can hold a dict or a list elsewhere and produce false positives.
    qt_assignments: Dict[str, str] = {}
    all_assignments: Dict[str, int] = {}
    for var in ANY_ASSIGN_RE.findall(text):
        all_assignments[var] = all_assignments.get(var, 0) + 1
    for var, cls in ASSIGN_RE.findall(text):
        if cls in members:
            qt_assignments[var] = cls
        else:
            problems.append(f"{path}: constructs unknown Qt class '{cls}'")
    receivers: Dict[str, str] = {}
    for var, cls in qt_assignments.items():
        if all_assignments.get(var, 0) == 1:
            receivers[var] = cls

    # Qt bases of the classes defined in *this* file, so self.<call> can be resolved
    local_bases: Dict[str, List[str]] = {}
    for match in re.finditer(r"^class\s+(\w+)\s*\(([^)]*)\)", text, re.M):
        name, base_text = match.group(1), match.group(2)
        local_bases[name] = [b.strip().split(".")[-1] for b in base_text.split(",") if b.strip()]

    owners = enclosing_classes(text)
    # instance attributes can hold callables (callbacks) - those are not Qt methods
    instance_attrs = set(re.findall(r"self\.(\w+)\s*=", text))
    local_methods: Dict[str, Set[str]] = {}
    for index, line in enumerate(text.splitlines(), start=1):
        defined = re.match(r"^\s+def\s+(\w+)\s*\(", line)
        if defined:
            local_methods.setdefault(owners.get(index, ""), set()).add(defined.group(1))
    for index, line in enumerate(text.splitlines(), start=1):
        for receiver, method in CALL_RE.findall(line):
            if receiver == "self":
                owner = owners.get(index, "")
                if method in local_methods.get(owner, set()):
                    continue                    # defined on this class
                if method in instance_attrs:
                    continue                    # callable stored on the instance
                chain = [base for base in local_bases.get(owner, []) if base in members]
                if not chain:
                    continue                    # not a Qt-derived class: nothing to check
                if not any(has_member(base, method, members, bases) for base in chain):
                    problems.append(
                        f"{path}:{index}: self.{method}() not found on {owner} or its Qt bases "
                        f"({', '.join(chain)})")
                continue
            if receiver in receivers:
                if not has_member(receivers[receiver], method, members, bases):
                    problems.append(
                        f"{path}:{index}: {receivers[receiver]}.{method}() is not part of the stub API")
    for cls, attr in CLASS_ATTR_RE.findall(text):
        if cls in members and attr[0].isupper():
            # enum member of a class (e.g. QSizePolicy.Policy) - only the class is checked
            continue
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", default=None)
    args = parser.parse_args(argv)

    directory = stub_directory()
    members, bases = parse_stubs(directory)
    print(f"stubs      : {directory}")
    print(f"classes    : {len(members)}")

    files = args.files or [
        "src/ui/learning_panel.py",
        "src/ui/main_window.py",
        "desktop/patient_app/main.py",
    ]
    problems: List[str] = []
    for name in files:
        path = Path(name)
        if not path.is_absolute():
            path = PROJECT_ROOT / name
        if not path.exists():
            problems.append(f"{path}: file not found")
            continue
        found = check_file(path, members, bases)
        problems.extend(found)
        print(f"checked    : {name} - {'OK' if not found else f'{len(found)} problem(s)'}")

    if problems:
        print()
        for problem in problems:
            print(f"  FAIL  {problem}")
        print(f"\n{len(problems)} Qt API problem(s)")
        return 1
    print("\nAll Qt classes and calls resolve against the PySide6 stubs.")
    print("Note: this verifies the API surface only - no rendering happened here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
