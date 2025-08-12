import logging
import datetime
import base64
import json
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

logger = logging.getLogger(__name__)

import re

class DeveloperToolsExtension(Extension):
    def __init__(self):
        super(DeveloperToolsExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, TimestampKeywordQueryEventListener())
        self.subscribe(KeywordQueryEvent, JwtKeywordQueryEventListener())
        self.subscribe(KeywordQueryEvent, Base64KeywordQueryEventListener())
        self.subscribe(KeywordQueryEvent, StringManipulationKeywordQueryEventListener())

class TimestampKeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['ts_keyword']:
            return

        query = event.get_argument() or ""

        if not query.strip():
             return RenderResultListAction([
                ExtensionResultItem(icon='images/clock.png',
                                  name='Timestamp Converter',
                                  description='Enter a unix timestamp or a date string',
                                  on_enter=HideWindowAction())
            ])

        # try to convert from timestamp
        try:
            timestamp = int(query)
            utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            local_dt = utc_dt.astimezone()
            items = [
                ExtensionResultItem(
                    icon='images/clock.png',
                    name=f"UTC: {utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}",
                    description='Copy to clipboard',
                    on_enter=CopyToClipboardAction(utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z'))
                ),
                ExtensionResultItem(
                    icon='images/clock.png',
                    name=f"Local: {local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}",
                    description='Copy to clipboard',
                    on_enter=CopyToClipboardAction(local_dt.strftime('%Y-%m-%d %H:%M:%S %Z'))
                )
            ]
            return RenderResultListAction(items)
        except (ValueError, OSError):
            pass

        # try to convert to timestamp
        try:
            dt = datetime.datetime.strptime(query, '%Y-%m-%d %H:%M:%S')
            timestamp = int(dt.timestamp())
            return RenderResultListAction([ExtensionResultItem(icon='images/clock.png', name=str(timestamp), description='Copy to clipboard', on_enter=CopyToClipboardAction(str(timestamp)))])
        except ValueError:
            return RenderResultListAction([ExtensionResultItem(icon='images/clock.png', name='Invalid input', description='Please enter a valid Unix timestamp or a date in YYYY-MM-DD HH:MM:SS format.', on_enter=HideWindowAction())])

class JwtKeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['jwt_keyword']:
            return

        token = event.get_argument()
        if not token:
            return RenderResultListAction([ExtensionResultItem(icon='images/jwt.png', name='Paste JWT token', description='Paste the JWT token to decode.', on_enter=HideWindowAction())])

        try:
            header, payload, signature = token.split('.')
            decoded_header = base64.b64decode(header + '==').decode('utf-8')
            decoded_payload = base64.b64decode(payload + '==').decode('utf-8')

            items = [
                ExtensionResultItem(
                    icon='images/jwt.png',
                    name='Header',
                    description=json.dumps(json.loads(decoded_header), indent=4),
                    on_enter=CopyToClipboardAction(json.dumps(json.loads(decoded_header), indent=4))
                ),
                ExtensionResultItem(
                    icon='images/jwt.png',
                    name='Payload',
                    description=json.dumps(json.loads(decoded_payload), indent=4),
                    on_enter=CopyToClipboardAction(json.dumps(json.loads(decoded_payload), indent=4))
                )
            ]
            return RenderResultListAction(items)
        except Exception as e:
            logger.error(e)
            return RenderResultListAction([ExtensionResultItem(icon='images/jwt.png', name='Invalid JWT token', description='Please enter a valid JWT token.', on_enter=HideWindowAction())])

class Base64KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['b64_keyword']:
            return

        query = event.get_argument() or ""
        parts = query.split(maxsplit=1)

        if len(parts) < 2:
            items = [
                ExtensionResultItem(
                    icon='images/b64.png',
                    name='Encode',
                    description='Encode a string to Base64.',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' encode ')
                ),
                ExtensionResultItem(
                    icon='images/b64.png',
                    name='Decode',
                    description='Decode a Base64 string.',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' decode ')
                )
            ]
            return RenderResultListAction(items)

        action = parts[0]
        text = parts[1]

        if action == 'encode':
            encoded_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return RenderResultListAction([ExtensionResultItem(icon='images/b64.png', name=encoded_text, description='Copy to clipboard', on_enter=CopyToClipboardAction(encoded_text))])
        elif action == 'decode':
            try:
                decoded_text = base64.b64decode(text).decode('utf-8')
                return RenderResultListAction([ExtensionResultItem(icon='images/b64.png', name=decoded_text, description='Copy to clipboard', on_enter=CopyToClipboardAction(decoded_text))])
            except:
                return RenderResultListAction([ExtensionResultItem(icon='images/b64.png', name='Invalid Base64 string', description='Please enter a valid Base64 string.', on_enter=HideWindowAction())])

class StringManipulationKeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['str_keyword']:
            return

        query = event.get_argument() or ""
        parts = query.split(maxsplit=1)

        if not query.strip():
            return RenderResultListAction([
                ExtensionResultItem(icon='images/string.png',
                                  name='String Manipulation',
                                  description='Enter a string and a command (e.g., "hello world upper")',
                                  on_enter=HideWindowAction())
            ])

        if len(parts) < 2:
            text = parts[0] if parts else ""
            items = [
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Remove special characters',
                    description='Remove special characters from the string',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' remove ' + text)
                ),
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Convert to UPPERCASE',
                    description='Convert text to UPPERCASE',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' upper ' + text)
                ),
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Convert to lowercase',
                    description='Convert text to lowercase',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' lower ' + text)
                ),
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Convert to CamelCase',
                    description='Convert to CamelCase',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' camel ' + text)
                ),
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Convert to snake_case',
                    description='Convert to snake_case',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' snake ' + text)
                ),
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Convert to kebab-case',
                    description='Convert to kebab-case',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' kebab ' + text)
                ),
                ExtensionResultItem(
                    icon='images/string.png',
                    name='Convert to Sentence case',
                    description='Convert to Sentence case',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' sentence ' + text)
                )
            ]
            return RenderResultListAction(items)

        command = parts[0]
        text = parts[1]
        result = ""

        if command == 'remove':
            result = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        elif command == 'upper':
            result = text.upper()
        elif command == 'lower':
            result = text.lower()
        elif command == 'camel':
            s = text.replace("-", " ").replace("_", " ")
            s = s.split()
            if len(s) == 0: return ""
            result = s[0].lower() + ''.join(word.capitalize() for word in s[1:])
        elif command == 'snake':
            s = text.replace("-", " ").replace(" ", "_")
            result = "".join([c.lower() if c.isalnum() else "_" for c in s])
            result = re.sub(r'_+', '_', result).strip('_')
        elif command == 'kebab':
            s = text.replace("_", " ").replace(" ", "-")
            result = "".join([c.lower() if c.isalnum() else "-" for c in s])
            result = re.sub(r'-+', '-', result).strip('-')
        elif command == 'sentence':
            if not text: return ""
            result = text.lower()
            result = result[0].upper() + result[1:]
            result = re.sub(r'([.!?]\s*)(\w)', lambda pat: pat.group(1) + pat.group(2).upper(), result)
        else:
            return RenderResultListAction([ExtensionResultItem(icon='images/string.png', name='Invalid command', description='Please enter a valid command.', on_enter=HideWindowAction())])

        return RenderResultListAction([ExtensionResultItem(icon='images/string.png', name=result, description='Copy to clipboard', on_enter=CopyToClipboardAction(result))])


if __name__ == '__main__':
    DeveloperToolsExtension().run()
