from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import finnhub

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"])

finnhub_client = finnhub.Client(api_key="cdinfiiad3i9g9pvtmm0cdinfiiad3i9g9pvtmmg")
current_price = finnhub_client.quote("AAPL")["c"]


@app.get("/")
async def index():
    return {"price": current_price}
