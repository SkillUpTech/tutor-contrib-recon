"""Functional interface similar to that of the builtin `json` module."""

import json
from pathlib import Path
from shutil import copy
from typing import MutableMapping, Optional

from .decoder import VJSONDecoder
from .encoder import VJSONEncoder
from .custom import VJSON_T
from ..cli import emit_critical, emit_warning


def load(source: Path, location: Path = None, **kwargs) -> MutableMapping:
    """Load the object stored at `source` using a VJSONDecoder."""
    if location is None:
        location = source.parent
    with open(source, "r") as f:
        return json.load(f, cls=VJSONDecoder, location=location, **kwargs)


def loads(s: str, **kwargs) -> MutableMapping:
    """Load the given VJSON-formatted string into a dict."""
    return json.loads(s, cls=VJSONDecoder, **kwargs)


def dump(
    obj: "MutableMapping[str, VJSON_T]",
    dest: Path,
    location: Path = None,
    write_remote_mappings: bool = True,
    expand_remote_mappings: bool = False,
    write_trailing_newline: bool = True,
    indent: Optional[int] = 4,
    backup: str = ".bak",
    **kwargs,
) -> None:
    """Dump the given object into the file specified by `dest` using a VJSONEncoder."""
    backup_path = None
    success = False
    if location is None:
        location = dest.parent
    if backup:
        backup_path = Path(str(dest) + backup)
        copy(dest, backup_path)
    try:
        with open(dest, "w") as f:
            json.dump(
                obj,
                f,
                cls=VJSONEncoder,
                indent=indent,
                location=location,
                write_remote_mappings=write_remote_mappings,
                expand_remote_mappings=expand_remote_mappings,
                **kwargs,
            )
            if write_trailing_newline:
                f.write("\n")
        success = True
    finally:
        if not success:
            if backup_path is not None:
                emit_warning(
                    f"An exception occurred while saving file '{dest}'. Restoring backup from '{backup_path}'."
                )
                backup_path.rename(dest)
            else:
                emit_critical(
                    f"Failed to save file '{dest}'. No backup was created, so you will probably have to manually fix the file.",
                    exit=True,
                )


def dumps(
    obj: "MutableMapping[str, VJSON_T]",
    location: Path = None,
    write_remote_mappings: bool = True,
    expand_remote_mappings: bool = False,
    indent: Optional[int] = 4,
    **kwargs,
) -> str:
    """Dump the given object as a VJSON-formatted string."""
    return json.dumps(
        obj,
        cls=VJSONEncoder,
        indent=indent,
        location=location,
        write_remote_mappings=write_remote_mappings,
        expand_remote_mappings=expand_remote_mappings,
        **kwargs,
    )
