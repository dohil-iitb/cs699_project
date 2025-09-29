import requests

url = "https://www.apollopharmacy.in/otc/pacimol-650mg-tablet?doNotTrack=true"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
print(response.text)