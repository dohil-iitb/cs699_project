import requests

url = "https://www.medplusmart.com/drugsInfo/medicines/central-nervous-system_20004/anxiolytics_30035"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
print(response.text)


