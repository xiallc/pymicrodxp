""" SPDX-License-Identifier: Apache-2.0 """
import argparse
import glob
import os
import shutil
import subprocess
import sys


def clean():
    """Removes old build, dist, and egg-info directories."""
    dirs_to_remove = ['build', 'dist', 'src/pymicrodxp.egg-info']

    print("\n--- Cleaning old artifacts ---")
    for d in dirs_to_remove:
        path = os.path.join(os.getcwd(), d)
        if os.path.exists(path):
            print(f"Removing {d}...")
            shutil.rmtree(path)
        else:
            print(f"Skipping {d} (does not exist)...")


def build():
    """Executes the standard python build module."""
    print("\n--- Executing Python Build ---")
    try:
        subprocess.check_call([sys.executable, '-m', 'build'])
        print("\n[SUCCESS] Build complete! Check the /dist directory.")
    except subprocess.CalledProcessError as e:
        print(f"\n[FAILED] Build process failed with error code: {e.returncode}")
        sys.exit(1)


def get_built_version() -> str:
    """Extracts the version from the generated wheel filename in the dist/ directory."""
    wheels = glob.glob(os.path.join('dist', '*.whl'))
    if not wheels:
        print("\n[FAILED] Could not find a .whl file in the dist/ directory to determine version.")
        sys.exit(1)

    whl_filename = os.path.basename(wheels[0])

    version = whl_filename.split('-')[1]
    return version


def validate_production_version(version: str):
    """Ensures the version is a clean release for Production PyPI."""
    print(f"\n--- Validating Version for Production: {version} ---")

    if "dev" in version or "+" in version:
        print("\n[ABORTED] Refusing to release a dirty/local version to Production.")
        print(
            "Ensure you are on a specific tag (e.g., git tag 1.0.0) with no uncommitted changes.")
        sys.exit(1)

    print("[SUCCESS] Version is clean for Production!")


def upload(target: str):
    """Uploads the dist directory to the specified PyPI target."""
    print(f"\n--- Uploading to {target.upper()} ---")

    cmd = [sys.executable, '-m', 'twine', 'upload']
    if target == 'testpypi':
        cmd.extend(['--repository', 'testpypi'])

    cmd.append('dist/*')

    try:
        subprocess.check_call(cmd)
        print(f"\n[SUCCESS] Upload to {target} complete!")
    except subprocess.CalledProcessError:
        print(f"\n[FAILED] Upload to {target} failed.")
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean, build, and deploy pymicrodxp.")
    parser.add_argument(
        'target',
        choices=['build', 'testpypi', 'pypi'],
        help="Action to perform: 'build' (local), 'testpypi' (upload to TestPyPI), or 'pypi' (upload to Production PyPI)."
    )

    args = parser.parse_args()

    clean()
    build()

    if args.target in ['testpypi', 'pypi']:
        version = get_built_version()

        if args.target == 'pypi':
            validate_production_version(version)
        else:
            print(f"\n--- TestPyPI Deployment: Proceeding with dev version '{version}' ---")

        upload(args.target)
