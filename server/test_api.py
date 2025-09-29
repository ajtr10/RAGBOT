import requests

resp = requests.post("http://localhost:8000/ask/", json={"question": "whats my name"})
print(resp.json())
