import json
import requests

def handler(request):
    try:
        # Get query string from request
        query = request.args if hasattr(request, "args") else request.GET
        link = query.get("link")

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

        resp = requests.get(url, headers=headers)
        resp.raise_for_status()  # Raise exception if status code != 200
        data = resp.json()

        return {
            "statusCode": 200,
            "body": json.dumps(data)
        }

    except requests.exceptions.RequestException as e:
        return {
            "statusCode": 502,
            "body": json.dumps({"error": "Failed to fetch from RapidAPI", "details": str(e)})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error", "details": str(e)})
        }
