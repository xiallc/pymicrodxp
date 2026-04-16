# Internal Release & Dev Guide

## Installation

If you are modifying the driver, adding new RS-232 commands, or writing tests, install the package
in "editable" mode with developer dependencies.

1. Activate your Virtual Environment.
2. Upgrade Build Tools: Ensure pip and setuptools are up to date to properly support pyproject.toml
   editable installs:
   ```
   python -m pip install --upgrade pip setuptools wheel
   ```
3. Install in Editable Mode with Dev Dependencies:
   ```
   pip install -e .[dev]
   ```
   This allows you to edit the source code in `src/pymicrodxp/` and see the changes immediately
   without reinstalling. It also installs testing frameworks like pytest.
4. Run the Test Suite:
   ```
   pytest
   ```

## Hardware Registry Management

The `pymicrodxp/core/registry.py` is the Single Source of Truth. When adding new firmware commands:

1. Add the command hex code.
2. Define the human-readable name.
3. Define specific `status_messages` for hardware error mapping.
4. Set `is_large: True` for spectrum or trace data to ensure they are suppressed at `INFO` log
   levels.

## Versioning Strategy

This project uses `setuptools-scm` to drive versioning dynamically via Git tags.
**Do not manually edit `__version__` in the source code.**

- **Drafting a Release**: Use Semantic Versioning.
- **Tagging**: `git tag -a 0.1.0 -m "Initial Release"`
- **Dev Builds**: If you have commits after a tag, `setuptools_scm` will automatically generate a
  `.devX` version suffix.

## Building & Releasing

We use a custom `release.py` script to automate building, enforcing version tags, and safely
uploading to PyPI via `twine`.

**1. To build a local distribution:**
Cleanly wipes the `dist/` and `build/` directories and generates a `.whl` and `.tar.gz`.

   ```
    python release.py build
   ```

**2. To deploy to TestPyPI:**
Uploads the local build to TestPyPI. (Allows `.dev` builds).

   ```
    python release.py testpypi
   ```

*To test the TestPyPI installation (falling back to PyPI for dependencies like `pyserial`):*

   ```
    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pymicrodxp
   ```

**3. To deploy an Official Release to Production PyPI:**
Enforces that your git tree is clean and explicitly on a version tag (blocks `.dev` releases).

   ```
    python release.py pypi
   ```

## Linux Post-Install Requirements

If users cannot access the hardware (Permission Denied), they must be added to the dialout group:

   ```
    sudo usermod -a -G dialout $USER
   ```

Users must log out and back in for this to take effect.