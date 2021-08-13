"""A custom JSON decoder and associated utilities."""

from json import JSONDecoder
from pathlib import Path
from tutor_recon.util.string import brief
from typing import TypeVar, Union
from enum import Enum

MARKER = '$'
ESCAPED_MARKER = MARKER * 2
UNSET_CONST_NAME = 'default'

JSON_T = TypeVar('JSON_T', str, int, float, bool, list, dict)
"""A type which can be represented in JSON."""


def escape(value: JSON_T = None) -> JSON_T:
    """If the value is a string beginning with '$', replace it with '$$'.
    
    Does not recursively descend into child objects.
    """
    if isinstance(value, str) and value.startswith('$'):
        return '$' + value
    return value

def format_unset(default: JSON_T, include_default = True, max_default_len=35) -> str:
    """Return '$default' with a parenthesized default value optionally added after a space."""
    if include_default:
        default = brief(repr(default), max_len=max_default_len)
        return f'${UNSET_CONST_NAME} ({default})'
    return f'${UNSET_CONST_NAME}'

class VJSONDecoder(JSONDecoder):
    """A custom JSON decoder which supports variable expansion along with references to objects in other files.
    
    Control sequences must occur at the beginning of an encoded string (key or value), 
        and are defined as follows:

    `$$`: A single `$` character.
    `$.`: Denotes the beginning of a relative path to anothor .json or .v.json spec to be substituted in its place.
          Always evaluates to an object.
    `$/`: Similar to above, but with an absolute path.
    `$` : Signifies the beginning of a variable name. 
          If given as a key, it is added along with its corresponding value to the rendering namespace.
          If given as a value, it is expanded to the corresponding value in the rendering namespace.

    Two-character control sequences are checked before one-character control sequences.

    A special built-in variable, `$default`, when given as a value (optionally followed by any sequence of characters,
    which are ignored), signifies that a keypair should be entirely ignored by the decoder. 
    
    Providing `$default`, or either path sequence, as a key is an error.

    The class can be instantiated with or without support for the relative path control sequence.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._csm = {
            ESCAPED_MARKER: lambda _: '$',
            MARKER + '/': self.expand_absolute,
            MARKER: self.handle_variable,
        }  # Stands for "control sequence mapping".

    @classmethod
    def fs_aware_decoder(cls, location: Path, *args, **kwargs) -> 'VJSONDecoder':
        """Create an instance which supports both path control sequences."""
        instance = cls(*args, **kwargs)
        instance._csm[MARKER + '.'] = lambda pair: instance.expand_relative(pair, location)
        return instance

    @classmethod
    def simple_decoder(cls, *args, **kwargs) -> 'VJSONDecoder':
        """Create an instance which only supports absolute path expansion."""
        return cls(*args, **kwargs)
