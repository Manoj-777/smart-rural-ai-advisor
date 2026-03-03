def handler(event, context):
    response = event.get('response', {})
    response['autoConfirmUser'] = True
    response['autoVerifyPhone'] = True
    event['response'] = response
    return event
