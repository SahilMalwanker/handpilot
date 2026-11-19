"""Read-only source checks for later Ubuntu use; no build or security guarantee."""

import argparse
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET


DOCS = (
    "PROJECT ARCHITECTURE CONTROL_SPEC ROS_INTERFACES ROBOT_MODEL TEST_PLAN "
    "VALIDATION_STATUS LEARNING_GUIDE TRANSFER_AND_SETUP RUN_AND_DEBUG "
    "RECORD_AND_REPLAY VISUALIZATION DEPENDENCIES ROADMAP TROUBLESHOOTING "
    "CAMERA_INTEGRATION_PLAN PUBLISH_FROM_MAC"
).split()
PACKAGE_FILES = {
    "handpilot_interfaces": ["CMakeLists.txt", "package.xml", "msg/TeleopCommand.msg",
                             "msg/ControllerStatus.msg", "srv/SetEngaged.srv"],
    "handpilot_core": ["CMakeLists.txt", "package.xml"] + [
        f"include/handpilot_core/{name}.hpp"
        for name in ("types", "planar_arm", "inverse_kinematics", "constraints", "controller")
    ] + [f"src/{name}.cpp" for name in ("planar_arm", "inverse_kinematics", "constraints", "controller")]
      + [f"test/test_{name}.cpp" for name in ("kinematics", "constraints", "controller")],
    "handpilot_control": ["CMakeLists.txt", "package.xml", "include/handpilot_control/controller_node.hpp",
                          "src/controller_node.cpp", "src/main.cpp", "test/test_controller_integration.py"],
    "handpilot_teleop": ["setup.py", "setup.cfg", "package.xml", "resource/handpilot_teleop",
                         "handpilot_teleop/__init__.py", "handpilot_teleop/keyboard_node.py",
                         "test/test_keyboard_mapping.py"],
    "handpilot_description": ["CMakeLists.txt", "package.xml", "urdf/planar_arm.urdf.xacro"],
    "handpilot_bringup": ["CMakeLists.txt", "package.xml", "launch/handpilot.launch.py",
                          "launch/visualization.launch.py", "config/controller.yaml", "foxglove/README.md"],
}
REQUIRED = ["README.md", "CONTRIBUTING.md", ".gitignore", ".gitattributes", ".editorconfig",
            "scripts/inspect_source.py", "scripts/README.md", ".github/copilot-instructions.md",
            ".github/workflows/ci.yml", ".github/pull_request_template.md",
            ".github/ISSUE_TEMPLATE/bug_report.md", ".github/ISSUE_TEMPLATE/feature_request.md"]
REQUIRED += [f"docs/{name}.md" for name in DOCS]
REQUIRED += [f"docs/decisions/{name}.md" for name in
             ("0001-ros-first", "0002-planar-arm", "0003-authoring-execution-split")]
REQUIRED += [f".github/instructions/{name}.instructions.md" for name in ("core", "ros", "tests", "docs")]
REQUIRED += [f".github/prompts/{name}.prompt.md" for name in
             ("implement-milestone", "review-controls", "diagnose-build", "prepare-release")]
REQUIRED += [f"src/{package}/{name}" for package, names in PACKAGE_FILES.items() for name in names]
GENERATED = {".git", "build", "install", "log", "__pycache__", ".pytest_cache", ".venv",
             "venv", "recordings", "results", "outputs", "local_results", "__MACOSX"}
TEXT_SUFFIXES = {".md", ".py", ".cpp", ".hpp", ".xml", ".xacro", ".yml", ".yaml", ".txt", ".cfg", ".msg", ".srv"}


def inspect(root: Path, transfer: bool) -> int:
    errors = []
    warnings = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"Missing required file: {relative}")
    for directory, folders, files in os.walk(root, followlinks=False):
        parent = Path(directory)
        for folder in list(folders):
            path = parent / folder
            if path.is_symlink():
                errors.append(f"Symlink directory not inspected: {path.relative_to(root)}")
                folders.remove(folder)
            elif folder in GENERATED or folder.endswith(".egg-info"):
                if transfer:
                    errors.append(f"Exclude from transfer: {path.relative_to(root)}")
                folders.remove(folder)
        for name in files:
            path = parent / name
            relative = path.relative_to(root)
            if path.is_symlink():
                errors.append(f"Symlink file not inspected: {relative}")
                continue
            if path.stat().st_size > 512 * 1024:
                errors.append(f"Suspiciously large source asset (>512 KiB): {relative}")
                continue
            if (name == ".env" or name.startswith(".env.") or name.endswith(".env")
                    or ".env." in name or path.suffix.lower() in {".zip", ".pyc", ".pyo", ".pem", ".key"}):
                errors.append(f"Review/exclude sensitive or generated file: {relative}")
            if path.suffix in TEXT_SUFFIXES or name in {".editorconfig", ".gitattributes", ".gitignore"}:
                data = path.read_bytes()
                if b"\r\n" in data:
                    warnings.append(f"CRLF text; normalize to LF before packaging: {relative}")
                if data and not data.endswith(b"\n"):
                    warnings.append(f"Missing final newline: {relative}")
                try:
                    data.decode("utf-8")
                except UnicodeDecodeError:
                    errors.append(f"Not UTF-8 text: {relative}")
            if path.suffix in {".xml", ".xacro"}:
                try:
                    document = ET.parse(path).getroot()
                except (ET.ParseError, OSError) as error:
                    errors.append(f"Malformed XML: {relative}: {error}")
                    continue
                if name == "package.xml":
                    if document.findtext("name") != parent.name:
                        errors.append(f"Package/directory name mismatch: {relative}")
                    maintainers = document.findall("maintainer")
                    if not maintainers or any(not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",
                                                               item.get("email", "")) for item in maintainers):
                        errors.append(f"Real maintainer email required before build: {relative}")
                    if document.findtext("license", "TODO") == "TODO":
                        warnings.append(f"License decision required before publication: {relative}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Source inspection only: {len(errors)} error(s), {len(warnings)} warning(s).")
    print("Does not compile, run tests, expand Xacro, validate ROS APIs, or prove security.")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transfer", action="store_true", help="also reject generated/recording/Git directories")
    arguments = parser.parse_args()
    return inspect(Path(__file__).resolve().parents[1], arguments.transfer)


if __name__ == "__main__":
    raise SystemExit(main())
