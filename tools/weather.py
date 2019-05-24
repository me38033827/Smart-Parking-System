import urllib.request
import json


def weather():
    url = "http://api.openweathermap.org/data/2.5/weather?zip=98467,us&appid=18673bd31365411ca390843bed5b6cba&units=Imperial"

    responese = urllib.request.urlopen(url)
    status = responese.status

    if status == 200:
        contents=responese.read()
        contents = contents.decode('utf-8')
        data = json.loads(contents)
    else:
        data=[]
    return data

