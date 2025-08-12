# Ulauncher Developer Tools

Ulauncher plugin with helpful tools for developers.

## Features

- ts — Timestamp Converter: Convert a Unix timestamp to a human-readable date (and vice versa).
- jwt — JWT Decoder: Decode a JWT token (header and payload).
- b64 — Base64 Encoder/Decoder: Encode or decode a string to/from Base64.
- str — String Manipulation: Convert strings to different cases (UPPERCASE, lowercase, CamelCase, snake_case, kebab-case, Sentence case) and remove special characters.

## Usage

1. Open Ulauncher.
2. Type one of the prefixes to choose a tool:
   - ts — Timestamp Converter
   - jwt — JWT Decoder
   - b64 — Base64 Encoder/Decoder
   - str — String Manipulation
3. Add a space and your input after the prefix, then press Enter and follow the on-screen instructions.

### Examples

- ts 1700000000
  - Converts the Unix timestamp to a human-readable date. Typing ts alone opens the converter.
- jwt <paste-your-jwt-here>
  - Decodes the token’s header and payload.
- b64 Hello world
  - Encodes the text to Base64. Using a Base64 string (e.g., b64 SGVsbG8gd29ybGQ=) will decode it.
- str hello world
  - Shows transformations like UPPERCASE, lowercase, CamelCase, snake_case, kebab-case, Sentence case, and removing special characters.

Note: The prefixes can be customized in the extension’s preferences.
