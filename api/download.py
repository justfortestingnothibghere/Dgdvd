import json
import os
import requests

def handler(request):
    # Get link from query params
    link = request.args.get('link')
    if not link:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'link' parameter"})
        }

    url = f"https://terabox-direct-download.p.rapidapi.com/?link={link}"

    headers = {
        "x-rapidapi-host": "terabox-direct-download.p.rapidapi.com",
        "x-rapidapi-key": "4d82a810eamshd39a55f3f19e967p19eaddjsn72b6603a9261"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    return {
        "statusCode": 200,
        "body": json.dumps(data)
    }
