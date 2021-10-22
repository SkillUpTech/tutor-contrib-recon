from abc import ABC, abstractmethod
import json
from json import JSONEncoder
from pathlib import Path
from typing import MutableMapping, Optional

from .util import WrappedDict, set_nested, walk_dict
from .constants import JSON_T, MARKER


class RemoteReferenceMixin(ABC):
    def __init__(self, *, remote_reference: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.remote_reference = remote_reference

    def reference_str(
        self, make_relative_to: Optional[Path] = None, safe: bool = False
    ) -> str:
        """The absolute or relative control sequence string used to reference the object.

        Keyword Arguments:
            make_relative_to: If set to a Path, absolute references will be converted to relative
                references with respect to the given path. Defaults to `None` (no conversion).
            safe: Use the absolute path instead if `make_relative_to` is not a parent of this
                `RemoteReference`'s target.

        Raises:
            ValueError: if the target of this mapping is not a subpath of `make_relative_to` and
                `safe=True` was not provided to the constructor.
        """
        if self.remote_reference.is_absolute():
            if make_relative_to is not None:
                try:
                    return self._target_relative(make_relative_to)
                except ValueError:
                    if safe:
                        return self._target_absolute()
                    raise
            return self._target_absolute()
        return self._target_relative()

    def _target_relative(self, to: Path = None) -> str:
        if to is not None:
            return f"{MARKER}+{self.remote_reference.relative_to(to)}"
        return f"{MARKER}+{self.remote_reference}"

    def _target_absolute(self) -> str:
        return f"{MARKER}+{self.remote_reference}"

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
        """Serialize the contents of this reference into its target file."""
        target = self.remote_reference
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


def expand_references(mapping: MutableMapping) -> dict:
    """Recursively expand any remote references within `mapping`."""
    ret = dict()
    for keys, val in walk_dict(mapping):
        if isinstance(val, RemoteReferenceMixin):
            set_nested(ret, keys, val.expand())
        else:
            set_nested(ret, keys, val)
    return ret
