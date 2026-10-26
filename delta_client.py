"""
Delta Exchange API Client supporting both Public Market Data and Authenticated Private Endpoints.
Configured for Delta Exchange India (api.india.delta.exchange) and Global (api.delta.exchange).
"""
import time
import hmac
import hashlib
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from models import ContractQuote, InstrumentKind, ValidationStatus
from config import config

class DeltaClient:
    def __init__(
        self, 
        base_url: Optional[str] = None, 
        api_key: Optional[str] = None, 
        api_secret: Optional[str] = None
    ):
        self.base_url = (base_url or config.DELTA_BASE_URL).rstrip("/")
        self.api_key = api_key or config.DELTA_API_KEY
        self.api_secret = api_secret or config.DELTA_API_SECRET
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "DeltaBacktestEngine/1.0",
            "Accept": "application/json"
        })

    def _generate_signature(
        self, 
        method: str, 
        path: str, 
        query_string: str = "", 
        body: str = "", 
        timestamp: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate Delta Exchange HMAC-SHA256 signature:
        message = method + timestamp + path + query_string + body
        """
        ts = timestamp or str(int(time.time()))
        message = method.upper() + ts + path + query_string + body
        sig = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return sig, ts

    def _auth_headers(
        self, 
        method: str, 
        path: str, 
        query_string: str = "", 
        body: str = ""
    ) -> Dict[str, str]:
        """Generate authentication headers for private endpoints."""
        if not self.api_key or not self.api_secret:
            return {}
        sig, ts = self._generate_signature(method, path, query_string, body)
        return {
            "api-key": self.api_key,
            "timestamp": ts,
            "signature": sig,
            "Content-Type": "application/json"
        }

    # -------------------------------------------------------------------------
    # Public Market Data Endpoints (No API key required)
    # -------------------------------------------------------------------------
    def get_option_products(self, underlying: str = "BTC") -> List[Dict[str, Any]]:
        """Fetch all active call and put option contracts for the given underlying."""
        endpoint = f"{self.base_url}/v2/products"
        params = {"contract_types": "call_options,put_options"}
        try:
            resp = self.session.get(endpoint, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("result", [])
            return [
                p for p in data 
                if p.get("underlying_asset", {}).get("symbol") == underlying
            ]
        except Exception as e:
            print(f"[DeltaClient] Error fetching products: {e}")
            return []

    def get_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all tickers indexed by product symbol."""
        endpoint = f"{self.base_url}/v2/tickers"
        try:
            resp = self.session.get(endpoint, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("result", [])
            return {t.get("symbol", ""): t for t in data}
        except Exception as e:
            print(f"[DeltaClient] Error fetching tickers: {e}")
            return {}

    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch current ticker / quotes for a symbol."""
        endpoint = f"{self.base_url}/v2/tickers/{symbol}"
        try:
            resp = self.session.get(endpoint, timeout=5)
            resp.raise_for_status()
            return resp.json().get("result")
        except Exception as e:
            print(f"[DeltaClient] Error fetching ticker for {symbol}: {e}")
            return None

    def get_l2_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch L2 orderbook (bids and asks) for a symbol."""
        endpoint = f"{self.base_url}/v2/l2orderbook/{symbol}"
        try:
            resp = self.session.get(endpoint, timeout=5)
            resp.raise_for_status()
            return resp.json().get("result")
        except Exception as e:
            print(f"[DeltaClient] Error fetching orderbook for {symbol}: {e}")
            return None

    # -------------------------------------------------------------------------
    # Private Authenticated Endpoints (Requires read-only API key & secret)
    # -------------------------------------------------------------------------
    def get_balances(self) -> Dict[str, Any]:
        """Fetch user wallet balances and net equity."""
        path = "/v2/wallet/balances"
        headers = self._auth_headers("GET", path)
        if not headers:
            return {"error": "API Key or Secret missing in configuration"}
        try:
            resp = self.session.get(self.base_url + path, headers=headers, timeout=6)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_positions(self) -> Dict[str, Any]:
        """Fetch open margined positions."""
        path = "/v2/positions/margined"
        headers = self._auth_headers("GET", path)
        if not headers:
            return {"error": "API Key or Secret missing"}
        try:
            resp = self.session.get(self.base_url + path, headers=headers, timeout=6)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
