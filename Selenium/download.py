import requests

url = 'url'
r = requests.get(url, stream=True)
name = url[50:-36]
with open(name, 'wb') as f:
    f.write(r.content)
