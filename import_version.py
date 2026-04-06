"""Doing this and that."""

from importlib import metadata


def list_non_standard_packages() -> None:
    """list_non_standard_packages."""
    # Common core packages to exclude
    core_packages = {
        # 'pip',
    }

    # Get all installed distributions
    dists = metadata.distributions()

    installed_list: list[str] = []

    for dist in dists:
        name = dist.metadata["Name"]
        version = dist.version

        # Check if it's a core package
        if name.lower() in core_packages:
            continue

        # Standard library modules don't have 'dist-info' metadata files
        # in the same way third-party packages do.
        installed_list.append(f"{name}=={version}")

    # Sort and print the results
    for package in sorted(installed_list, key=lambda x: x.lower()):
        print(type(package))  # noqa: T201
        print(package)  # noqa: T201


if __name__ == "__main__":
    list_non_standard_packages()
