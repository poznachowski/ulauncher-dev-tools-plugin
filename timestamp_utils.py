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


def uuidv7_to_datetime_string(uuid_str: str) -> str:
    """
    Extract timestamp from UUIDv7 and convert to ISO 8601 format string.

    UUIDv7 format (RFC 9562):
    - First 48 bits (12 hex chars) contain Unix timestamp in milliseconds
    - Version field (4 bits) at bits 48-51 must be 0111 (7)
    - Variant field (2 bits) at bits 64-65 must be 10

    Args:
        uuid_str: UUIDv7 string with or without hyphens

    Returns:
        ISO 8601 formatted datetime string like '2025-10-02T12:58:46.991Z'

    Raises:
        ValueError: If the UUID format is invalid or not version 7
    """
    # Remove hyphens if present
    clean_uuid = uuid_str.replace('-', '').strip()

    # Validate length (UUID should be 32 hex chars)
    if len(clean_uuid) != 32:
        raise ValueError(f"Invalid UUID length: expected 32 hex chars, got {len(clean_uuid)}")

    try:
        # Validate hex characters
        int(clean_uuid, 16)
    except ValueError:
        raise ValueError("UUID contains invalid hexadecimal characters")

    # Check version field (bits 48-51, which is the first hex digit at position 12)
    # In standard UUID format: xxxxxxxx-xxxx-Vxxx-xxxx-xxxxxxxxxxxx
    # Position 12 in clean string (0-indexed) is the version digit
    version_hex = clean_uuid[12]
    version = int(version_hex, 16)

    # The high nibble contains the version, should be 0111 (7) for UUIDv7
    # In practice, the version hex digit should be '7'
    if version != 7:
        raise ValueError(f"Not a UUIDv7: version field is {version}, expected 7")

    # Check variant field (bits 64-65, which is at position 16)
    # The variant should be 10xx (RFC 4122/9562 variant)
    variant_hex = clean_uuid[16]
    variant_value = int(variant_hex, 16)
    # Variant bits should be 10xx, meaning the hex value should be 8, 9, A, or B
    if variant_value not in (8, 9, 0xA, 0xB):
        raise ValueError(f"Invalid UUID variant: expected RFC 4122 variant (8, 9, A, or B), got {variant_hex}")

    try:
        # Extract first 48 bits (12 hex characters)
        timestamp_hex = clean_uuid[:12]
        timestamp_ms = int(timestamp_hex, 16)

        # Convert to datetime
        timestamp_seconds = timestamp_ms / 1000.0
        dt = datetime.datetime.fromtimestamp(timestamp_seconds, tz=datetime.timezone.utc)

        # Format as ISO 8601 with milliseconds
        # Format: YYYY-MM-DDTHH:MM:SS.sssZ
        iso_string = dt.strftime('%Y-%m-%dT%H:%M:%S')
        # Add milliseconds
        milliseconds = timestamp_ms % 1000
        iso_string = f"{iso_string}.{milliseconds:03d}Z"

        return iso_string
    except (ValueError, OverflowError) as e:
        raise ValueError(f"Invalid UUID format or timestamp: {e}")