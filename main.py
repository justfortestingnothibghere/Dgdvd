from flask import Flask, request, Response, jsonify
import requests

app = Flask(__name__)

# Default fallback cookie
DEFAULT_COOKIE = "ndus=Y2YqaCTteHuiU3Ud_MYU7vHoVW4DNBi0MPmg_1tQ"

# Function to prepare headers
def get_dl_headers(cookie=None, range_header=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://1024terabox.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cookie": cookie or DEFAULT_COOKIE,
    }
    if range_header:
        headers['Range'] = range_header
    return headers

# CORS headers
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Range",
    "Access-Control-Expose-Headers": "Content-Length,Content-Range,Content-Disposition"
}

@app.route("/download", methods=["GET", "OPTIONS"])
def download_file():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        resp = Response()
        for k, v in CORS_HEADERS.items():
            resp.headers[k] = v
        return resp

    # Get query params
    download_url = request.args.get("url")
    file_name = request.args.get("filename")
    cookie = request.args.get("cookie")
    range_header = request.headers.get("Range")

    if not download_url:
        return jsonify({"error": "Missing required parameter: url"}), 400

    try:
        headers = get_dl_headers(cookie, range_header)
        resp = requests.get(download_url, headers=headers, stream=True, allow_redirects=True)

        if not resp.ok and resp.status_code != 206:
            return jsonify({"error": "Download service temporarily unavailable"}), 502

        # Prepare response
        response = Response(resp.raw, status=resp.status_code, content_type=resp.headers.get("Content-Type", "application/octet-stream"))

        # Add CORS + caching headers
        for k, v in CORS_HEADERS.items():
            response.headers[k] = v
        response.headers["Cache-Control"] = "public, max-age=3600"

        # Filename header
        if file_name:
            response.headers["Content-Disposition"] = f'inline; filename="{file_name}"'

        # Range headers
        if "Content-Range" in resp.headers:
            response.headers["Content-Range"] = resp.headers["Content-Range"]
            response.headers["Accept-Ranges"] = "bytes"

        if "Content-Length" in resp.headers:
            response.headers["Content-Length"] = resp.headers["Content-Length"]

        return response

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Download service error occurred"}), 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
