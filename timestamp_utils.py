import datetime

def normalize_epoch_to_millis(value: int | float | str) -> int:
    """
    Normalize an epoch timestamp of varying precision to milliseconds (int).

    Accepts seconds, milliseconds, microseconds, or nanoseconds (as int/float/str),
    and returns milliseconds as int.

    Heuristics based on absolute magnitude:
    - >= 1e18: nanoseconds -> // 1e6
    - >= 1e15: microseconds -> // 1e3
    - >= 1e12: milliseconds  -> as-is
    - else:    seconds       -> * 1000
    """
    if isinstance(value, str):
        value = value.strip()
        v = float(value)
    elif isinstance(value, (int, float)):
        v = float(value)
    else:
        raise TypeError(f"Unsupported type for epoch value: {type(value)!r}")

    av = abs(v)

    if av >= 1e18:  # ns
        ms = v / 1e6
    elif av >= 1e15:  # µs
        ms = v / 1e3
    elif av >= 1e12:  # ms
        ms = v
    else:  # s
        ms = v * 1000.0
    # floor towards zero to get stable int milliseconds
    return int(ms)



def unix_to_utc_local_strings(timestamp: int | float | str) -> tuple[str, str]:
    """
    Convert a Unix timestamp (seconds/ms/us/ns) to formatted UTC and local time strings.
    Internally normalizes to milliseconds and converts to seconds for datetime.
    Returns (utc_str, local_str) with format '%Y-%m-%d %H:%M:%S.%f %Z' truncated to milliseconds.
    """
    ms = normalize_epoch_to_millis(timestamp)
    seconds = ms / 1000.0
    utc_dt = datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
    local_dt = utc_dt.astimezone()

    def _fmt_ms(dt: datetime.datetime) -> str:
        # Format with microseconds then truncate to 3 digits for milliseconds
        s = dt.strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        # Replace .abcdef with .abc
        dot = s.rfind('.')
        if dot != -1:
            # Keep 3 digits after dot, before the space preceding TZ
            before_tz = s[:s.rfind(' ')]
            tz = s[s.rfind(' ') + 1:]
            ms_part = before_tz[dot + 1:dot + 4]
            return f"{before_tz[:dot]}.{ms_part} {tz}"
        return s

    utc_str = _fmt_ms(utc_dt)
    local_str = _fmt_ms(local_dt)
    return utc_str, local_str

def datestr_to_unix(date_str: str) -> int:
    """
    Parse a local naive datetime string in '%Y-%m-%d %H:%M:%S' and return Unix timestamp (seconds, int).
    Kept for backward compatibility.
    """
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return int(dt.timestamp())

def datestr_to_unix_millis(date_str: str) -> int:
    """
    Parse a local naive datetime string in '%Y-%m-%d %H:%M:%S' and return Unix timestamp in milliseconds (int).
    """
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return int(dt.timestamp() * 1000.0)


def iso_instant_to_unix_millis(iso_str: str) -> int:
    """
    Parse an ISO_INSTANT string like '2011-12-03T10:15:30Z' or '2007-12-03T10:15:30.00Z'
    and return Unix timestamp in milliseconds (int). ISO_INSTANT is always UTC (Z).
    """
    s = iso_str.strip()
    if not s.endswith("Z") and not s.endswith("z"):
        # For strict ISO_INSTANT, require 'Z'; but allow offset form as fallback if present
        # Try to parse offsets like +00:00 as well
        try:
            dt = datetime.datetime.fromisoformat(s)
            if dt.tzinfo is None:
                # Treat naive as UTC if it looks like instant
                dt = dt.replace(tzinfo=datetime.timezone.utc)
        except Exception:
            # Try explicit formats with fractional seconds and without
            try:
                dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%z")
            except Exception:
                dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
        return int(dt.timestamp() * 1000)

    # Normalize Z -> +00:00 for fromisoformat
    s_norm = s[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(s_norm)
    except ValueError:
        # Fallbacks to be extra robust
        try:
            dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp() * 1000)


