import re
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path


def project_version(toml_header="[tool.poetry]"):
    """Get the version number of the root module in which this function resides.

    - Supports reading from pyproject.toml in case the project is not actually installed.
    - This should work no matter where in the hierarchy this function is placed, though the program
      *must* be running as a module (either imported or run with 'python -m ...').

    Arguments:
        toml_header (str): The header in the project's 'pyproject.toml' which contains the project's 'version'.
            Only used if this project is not installed. Defaults to '[tool.poetry]'.

    Returns:
        ver (str): The version number of the project.

    Raises:
        AttributeError: If this function is not running as part of a module.
        FileNotFoundError: If the version number couldn't be obtained from importlib, but there is also no
            'pyproject.toml' at the root of the project.
        KeyError: If the version number couldn't be obtained from importlib, and a 'pyproject.toml' file was found,
            but no version number was found in the file.
    """
    qualname = (__spec__.name if __name__ == "__main__" else __name__).split(".")
    mainname = qualname[0]
    try:
        ver = version(mainname)
    except PackageNotFoundError:
        toml_header = re.escape(toml_header)
        depth = len(qualname) - 1
        with open(Path(__file__).parents[depth] / "pyproject.toml", "r") as pyproj:
            toml_text = pyproj.read()
        match = re.search(
            rf'^{toml_header}$[^^\[]*^version = "([^"]+)"$', toml_text, re.MULTILINE
        )
        if not match:
            raise KeyError('No version specification was found in pyproject.toml.')
        ver = match.group(1)
    return ver

__version__ = project_version()
