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
        write_remote_mappings: bool = False,
        expand_remote_mappings: bool = False,
        prefer_relative_references: bool = True,
        **kwargs,
    ) -> None:
        """
        Keyword Arguments:
            location (Path): The base path to use when expanding relative references.
            write_remote_mappings (bool): Whether to update the files corresponding to
                remote references during serialization.
            expand_remote_mappings (bool): If True, write the content of the files corresponding
                to remote references directly in the output file.
            prefer_relative_references (bool): Always write out relative references when possible.
                Has no effect if `location` is not set.
        **kwargs:
            Passed to `super().__init__`.
        """
        self.write_remote_mappings = write_remote_mappings
        self.expand_remote_mappings = expand_remote_mappings
        self.prefer_relative_references = prefer_relative_references
        self.location = location
        kwargs.pop("location", None)
        self._params = kwargs.copy()
        super().__init__(**kwargs)

    def params(self) -> dict:
        """Return a dictionary of all keyword arguments used to instantiate this object apart from `location`."""
        return self._params.copy()

    def default(self, o: VJSON_T) -> JSON_T:
        if isinstance(o, RemoteReferenceMixin):
            if self.write_remote_mappings:
                o.write(type(self), location=self.location, **self.params())
            if self.expand_remote_mappings:
                return o.expand()
            if self.location and self.prefer_relative_references:
                return o.reference_str(make_relative_to=self.location)
            return o.reference_str()
        if isinstance(o, VJSONSerializableMixin):
            return o.to_object()
        return super().default(o)
