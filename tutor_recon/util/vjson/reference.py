from abc import ABC, abstractmethod
import json
from json import JSONEncoder
from pathlib import Path
from typing import MutableMapping, Optional

from .util import WrappedDict, set_nested, walk_dict
from .constants import JSON_T, MARKER


class RemoteReferenceMixin(ABC):
    def __init__(self, *, target: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.target = target

    @property
    def reference_str(self) -> str:
        """The absolute or relative control sequence string used to reference the object."""
        if self.target.is_absolute():
            return f"{MARKER}/{self.target}"
        return f"{MARKER}./{self.target}"

    @abstractmethod
    def expand(self) -> JSON_T:
        """Return the referenced data."""

    def write(
        self,
        serializer: "type[JSONEncoder]" = JSONEncoder,
        location: Optional[Path] = None,
        write_trailing_newline: bool = True,
        **kwargs,
    ) -> None:
        """Serialize the contents of this mapping to its target."""
        target = self.target
        if not target.is_absolute():
            assert (
                location
            ), f"Cannot write to relative path '{target}' without a location specified."
            target = location / target
        target.parent.mkdir(exist_ok=True, parents=True)
        with open(target, "w") as f:
            json.dump(self.expand(), f, cls=serializer, location=location, **kwargs)
            if write_trailing_newline:
                f.write("\n")


class RemoteMapping(RemoteReferenceMixin, WrappedDict):
    """A dict-like reference to a JSON mapping (object) stored in another file."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def expand(self) -> dict:
        return self._dict


def expand_mappings(mapping: MutableMapping) -> dict:
    """Recursively expand any remote mappings within `mapping`."""
    ret = dict()
    for keys, val in walk_dict(mapping):
        if isinstance(val, RemoteMapping):
            set_nested(ret, keys, val.expand())
        else:
            set_nested(ret, keys, val)
    return ret
