import requests

url = "  https://browser.geekbench.com/v6/cpu/15619162/claim?key=787989"

response = requests.get(url)

# Raise error if request failed
response.raise_for_status()

html_content = response.text
print(html_content)
