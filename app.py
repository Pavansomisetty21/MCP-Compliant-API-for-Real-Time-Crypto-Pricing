"""
This Flask script provides an API to fetch the current price of a cryptocurrency
using the CoinGecko API.
"""
import httpx
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

app = Flask(__name__)

async def fetch_crypto_price(crypto_id: str, currency: str = "usd") -> str:
    """
    Fetches the current price of a cryptocurrency in the specified currency.
    """
    url = f"{COINGECKO_BASE_URL}/simple/price"
    params = {
        "ids": crypto_id,
        "vs_currencies": currency
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if crypto_id not in data:
                return f"Cryptocurrency '{crypto_id}' not found. Please check the ID and try again."
            price = data[crypto_id][currency]
            return f"The current price of {crypto_id} is {price} {currency.upper()}"
    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Error fetching price data: {str(e)}"

@app.route("/crypto-price", methods=["POST"])
def get_crypto_price():
    """
    POST API to get the crypto price.
    Example JSON input: {"crypto_id": "bitcoin", "currency": "usd"}
    """
    data = request.get_json()
    if not data or "crypto_id" not in data:
        return jsonify({"error": "Missing 'crypto_id' in request"}), 400

    crypto_id = data["crypto_id"]
    currency = data.get("currency", "usd")

    # Run the async fetch function in sync context using asyncio
    import asyncio
    result = asyncio.run(fetch_crypto_price(crypto_id, currency))

    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(debug=True)
