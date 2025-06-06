"""
This script sets up both:
1. An MCP server using FastMCP
2. A Flask POST API for calling the same crypto price tool
"""

import httpx
import asyncio
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Initialize FastMCP
mcp = FastMCP("crypto_price_tracker")

# Register MCP tool (used by MCP server or programmatically reused)
@mcp.tool()
async def get_crypto_price(crypto_id: str, currency: str = "usd") -> str:
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

# ---------- Flask API ----------
app = Flask(__name__)

@app.route("/crypto-price", methods=["POST"])
def flask_crypto_price():
    """
    Flask POST endpoint for getting the crypto price.
    """
    data = request.get_json()
    if not data or "crypto_id" not in data:
        return jsonify({"error": "Missing 'crypto_id'"}), 400

    crypto_id = data["crypto_id"]
    currency = data.get("currency", "usd")

    result = asyncio.run(get_crypto_price(crypto_id, currency))
    return jsonify({"result": result})

# ---------- Entrypoint ----------
if __name__ == "__main__":
    import threading

    # Start MCP server in a background thread
    def run_mcp():
        mcp.run()

    threading.Thread(target=run_mcp, daemon=True).start()

    # Start Flask server
    app.run(debug=True, port=5000)
