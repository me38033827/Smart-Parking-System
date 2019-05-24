import urllib.request
import json


def price():
    url = "http://devapi.mygasfeed.com/stations/details/103920/rfej9napna.json"

    responese = urllib.request.urlopen(url)
    status=responese.status

    if status==200:
        contents=responese.read()
        contents = contents.decode('utf-8')

        data = json.loads(contents)
    else:
        data=[]

    return data


