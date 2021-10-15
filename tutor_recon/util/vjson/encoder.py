"""The VJSONEncoder definition."""

from json import JSONEncoder
from typing import Optional
from pathlib import Path

from .constants import JSON_T
from .reference import RemoteReferenceMixin
from .custom import VJSONSerializableMixin, VJSON_T


class VJSONEncoder(JSONEncoder):
    """Serializer counterpart to `VJSONDecoder`.

    See `VJSONDecoder` for further information.
    """

    def __init__(
        self,
        location: Optional[Path] = None,
        **kwargs,
    ) -> None:
        """
        **kwargs:
            location (Path): The base path to use when expanding relative references.
            write_remote_mappings (bool): Whether to update the files corresponding to
                remote references during serialization.
            expand_remote_mappings (bool): If True, write the content of the files corresponding
                to remote references directly in the output file.
            - Remaining arguments are passed to JSONEncoder.__init__().
        """
        self._params = kwargs.copy()
        self.write_remote_mappings = kwargs.pop("write_remote_mappings")
        self.expand_remote_mappings = kwargs.pop("expand_remote_mappings")
        self.location = location
        super().__init__(**kwargs)

    def params(self) -> dict:
        """Return a dictionary of all keyword arguments used to instantiate this object apart from `location`."""
        return self._params.copy()

    def default(self, o: VJSON_T) -> JSON_T:
        if isinstance(o, RemoteReferenceMixin):
            if self.write_remote_mappings:
                o.write(type(self), self.location, **self.params())
            if self.expand_remote_mappings:
                return o.expand()
            return o.reference_str
        if isinstance(o, VJSONSerializableMixin):
            return o.to_object()
        return super().default(o)
