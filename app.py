import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.dependencies import CurrentAccessToken
from fastmcp.server.auth import OAuthProxy, AccessToken, TokenVerifier
from pypco import PCO

load_dotenv()


# =============================================================================
# OAuth Authentication
# =============================================================================

class PCOTokenVerifier(TokenVerifier):
    """Validates PCO OAuth tokens by calling the PCO API."""

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.planningcenteronline.com/people/v2/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                if resp.status_code != 200:
                    return None

                data = resp.json()["data"]
                attrs = data["attributes"]

                return AccessToken(
                    token=token,
                    client_id="pco",
                    scopes=["services", "people"],
                    claims={
                        "sub": data["id"],
                        "name": f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip(),
                        "email": attrs.get("primary_email_address"),
                        "pco_access_token": token,
                    },
                )
        except Exception:
            return None


auth = OAuthProxy(
    upstream_authorization_endpoint="https://api.planningcenteronline.com/oauth/authorize",
    upstream_token_endpoint="https://api.planningcenteronline.com/oauth/token",
    upstream_client_id=os.environ["PCO_CLIENT_ID"],
    upstream_client_secret=os.environ["PCO_CLIENT_SECRET"],
    token_verifier=PCOTokenVerifier(),
    base_url=os.environ.get("BASE_URL", "http://localhost:8000"),
    extra_authorize_params={"scope": "services people registrations giving calendar"},
    jwt_signing_key=os.environ.get("JWT_SIGNING_KEY"),
)

mcp = FastMCP("PCO MCP Server", auth=auth)


# =============================================================================
# Per-User PCO Client
# =============================================================================

async def get_pco(token: AccessToken = CurrentAccessToken()) -> PCO:
    """Create a per-user PCO client from the authenticated user's upstream token."""
    upstream_token = token.claims.get("pco_access_token")
    if not upstream_token:
        raise ValueError("No PCO access token available")
    return PCO(token=upstream_token)


def _build_patch_body(resource_type: str, **kwargs) -> dict:
    """Build a JSON:API PATCH body with only non-None attributes."""
    attributes = {k: v for k, v in kwargs.items() if v is not None}
    return {
        "data": {
            "type": resource_type,
            "attributes": attributes
        }
    }
