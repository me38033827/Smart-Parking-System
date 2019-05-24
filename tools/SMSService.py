import nexmo


def sendSMS(phone):
    client = nexmo.Client(key='96a06b22', secret='pjos0009lK3a255W')

    client.send_message({
        'from': '12092835063',
        'to': '1'+phone,
        'text': 'Notification:\nThere are 20 minutes before your parking time reaches 3 hours!',
    })



