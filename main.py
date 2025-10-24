from fastapi import FastAPI, Query
import requests
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

RAPIDAPI_KEY = "4d82a810eamshd39a55f3f19e967p19eaddjsn72b6603a9261"

@app.get("/download")
async def download(link: str = Query(..., description="Terabox file share link")):
    try:
        url = f"https://terabox-direct-download.p.rapidapi.com/?link={link}"
        headers = {
            "x-rapidapi-host": "terabox-direct-download.p.rapidapi.com",
            "x-rapidapi-key": RAPIDAPI_KEY
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return JSONResponse(content=data)
    except requests.exceptions.RequestException as e:
        return JSONResponse(content={"error": "Failed to fetch from RapidAPI", "details": str(e)}, status_code=502)
    except Exception as e:
        return JSONResponse(content={"error": "Internal server error", "details": str(e)}, status_code=500)

# Only needed if running locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
