import urllib.parse

from pydantic import BaseModel


class AuthRequirements(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    token_url: str
    auth_url: str


class AuthCredentials(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


def get_credentials(auth_requirements: AuthRequirements) -> AuthCredentials:
    pass


def get_auth_url(auth_requirements: AuthRequirements) -> str:
    params = {
        "client_id": auth_requirements.client_id,
        "redirect_uri": auth_requirements.redirect_uri,
        "scope": " ".join(auth_requirements.scopes),
        "response_type": "code",
    }

    return auth_requirements.auth_url + "?" + urllib.parse.urlencode(params)
