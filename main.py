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

class DeveloperToolsExtension(Extension):
    def __init__(self):
        super(DeveloperToolsExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, TimestampKeywordQueryEventListener())
        self.subscribe(KeywordQueryEvent, JwtKeywordQueryEventListener())
        self.subscribe(KeywordQueryEvent, Base64KeywordQueryEventListener())

class TimestampKeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['ts_keyword']:
            return

        query = event.get_argument() or ""

        if not query.strip():
             return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
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
                    icon='images/icon.png',
                    name=f"UTC: {utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}",
                    description='Copy to clipboard',
                    on_enter=CopyToClipboardAction(utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z'))
                ),
                ExtensionResultItem(
                    icon='images/icon.png',
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
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name=str(timestamp), description='Copy to clipboard', on_enter=CopyToClipboardAction(str(timestamp)))])
        except ValueError:
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name='Invalid input', description='Please enter a valid Unix timestamp or a date in YYYY-MM-DD HH:MM:SS format.', on_enter=HideWindowAction())])

class JwtKeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['jwt_keyword']:
            return

        token = event.get_argument()
        if not token:
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name='Paste JWT token', description='Paste the JWT token to decode.', on_enter=HideWindowAction())])

        try:
            header, payload, signature = token.split('.')
            decoded_header = base64.b64decode(header + '==').decode('utf-8')
            decoded_payload = base64.b64decode(payload + '==').decode('utf-8')

            items = [
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Header',
                    description=json.dumps(json.loads(decoded_header), indent=4),
                    on_enter=CopyToClipboardAction(json.dumps(json.loads(decoded_header), indent=4))
                ),
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Payload',
                    description=json.dumps(json.loads(decoded_payload), indent=4),
                    on_enter=CopyToClipboardAction(json.dumps(json.loads(decoded_payload), indent=4))
                )
            ]
            return RenderResultListAction(items)
        except Exception as e:
            logger.error(e)
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name='Invalid JWT token', description='Please enter a valid JWT token.', on_enter=HideWindowAction())])

class Base64KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        if event.get_keyword() != extension.preferences['b64_keyword']:
            return

        query = event.get_argument() or ""
        parts = query.split(maxsplit=1)

        if len(parts) < 2:
            items = [
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Encode',
                    description='Encode a string to Base64.',
                    on_enter=SetUserQueryAction(event.get_keyword() + ' encode ')
                ),
                ExtensionResultItem(
                    icon='images/icon.png',
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
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name=encoded_text, description='Copy to clipboard', on_enter=CopyToClipboardAction(encoded_text))])
        elif action == 'decode':
            try:
                decoded_text = base64.b64decode(text).decode('utf-8')
                return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name=decoded_text, description='Copy to clipboard', on_enter=CopyToClipboardAction(decoded_text))])
            except:
                return RenderResultListAction([ExtensionResultItem(icon='images/icon.png', name='Invalid Base64 string', description='Please enter a valid Base64 string.', on_enter=HideWindowAction())])

if __name__ == '__main__':
    DeveloperToolsExtension().run()
