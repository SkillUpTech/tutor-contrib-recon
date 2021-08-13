"""String-related utilities."""

def brief(string: str, max_len=20) -> str:
    """Shorten the given string to a maximum length using elipses."""
    if len(string) > max_len:
        return string[:max_len - 3] + '...'
    return string
