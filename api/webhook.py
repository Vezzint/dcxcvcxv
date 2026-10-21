import json

def handler(event, context):
    # Здесь ваша логика обработки сообщений от Telegram
    # event содержит тело запроса от Telegram (в event['body'])
    return {
        "statusCode": 200,
        "body": json.dumps({"ok": True})
    }
