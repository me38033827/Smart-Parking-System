import nexmo


def sendSMS(text):
    client = nexmo.Client(key='96a06b22', secret='pjos0009lK3a255W')

    client.send_message({
        'from': '12092835063',
        'to': '12538837083',
        'text': text,
    })

sendSMS("hello world")




