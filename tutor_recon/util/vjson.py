"""A custom JSON decoder and associated utilities."""

from json import JSONDecoder


class VJSONDecoder(JSONDecoder):
    """A custom JSON decoder which supports variable expansion along with references to objects in other files."""
