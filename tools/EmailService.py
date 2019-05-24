from mailjet_rest import Client


def sendEmail(address,content):
    api_key = 'e77da58ef8e0ddaf4560c3d4e6a550dc'
    api_secret = '72c29d6b9b5a6acb111c9bd50b20a5b8'
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    # content="'2018-03-27', '14:09:04', '22:16:55'\n'2018-11-06', '21:48:11', '22:22:05'\n'2019-01-27', '07:26:07', '09:00:41'\n'2019-02-27', '20:51:05', '22:49:51'\n'2018-03-26', '11:46:45', '16:55:00'\n'2019-01-29', '13:09:18', '17:35:12'\n'2017-01-03', '19:39:01', '23:45:39'\n'2018-02-07', '10:38:36', '12:06:28'\n'2019-02-21', '22:54:19', '01:22:03'\n'2018-08-09', '21:22:26', '01:34:06'\n'2018-02-09', '07:47:23', '16:05:50'"


    data = {
      'Messages': [
                    {
                            "From": {
                                    "Email": "zhaohu@uw.edu",
                                    "Name": "parkManager"
                            },
                            "To": [
                                    {
                                            "Email": address,
                                            "Name": "Customer"
                                    }
                            ],
                            "Subject": "History parking records",
                            "TextPart": "Dear customer, this is your history parking records:\n\n"+content,

                    }
            ]
    }
    result = mailjet.send.create(data=data)
    print (result.status_code)
    print (result.json())
