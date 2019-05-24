import urllib.request
import json


def weather():
    url = "http://api.openweathermap.org/data/2.5/weather?zip=98467,us&appid=18673bd31365411ca390843bed5b6cba&units=Imperial"

    response = urllib.request.urlopen(url)
    status = response.status

    if status == 200:
        contents=response.read()
        contents = contents.decode('utf-8')
        data = json.loads(contents)
    else:
        data=[]
    return data


if __name__ == '__main__':
    print(weather())

