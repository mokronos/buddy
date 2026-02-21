import spotipy
from dotenv import load_dotenv
from fastmcp import Context, FastMCP
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

mcp = FastMCP("spotify")


def get_spotify_client(ctx: Context):
    """Create a Spotipy client using credentials from context deps."""
    deps = getattr(ctx.request_context.meta, "deps", {}) or {}
    print(deps)
    client_id = deps.get("spotify_client_id")
    client_secret = deps.get("spotify_client_secret")
    redirect_uri = deps.get("spotify_redirect_uri")
    user_id = deps.get("user_id", "default")

    if not client_id or not client_secret or not redirect_uri:
        raise ValueError("Missing Spotify API credentials in context deps.")

    cache_handler = CacheFileHandler(cache_path=f".cache-{user_id}")
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_handler=cache_handler,
        open_browser=False,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


@mcp.tool
def list_devices(ctx: Context) -> str:
    """Lists the available Spotify devices."""
    sp = get_spotify_client(ctx)
    devices = sp.devices()
    if not devices["devices"]:
        return "No active Spotify devices found."
    return "\n".join(f"{d['name']} ({d['type']}) - ID: {d['id']}" for d in devices["devices"])


@mcp.tool
def search_song(ctx: Context, query: str, limit: int = 5) -> str:
    """Searches for a song on Spotify."""
    sp = get_spotify_client(ctx)
    results = sp.search(q=query, type="track", limit=limit)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return "No songs found."
    return "\n".join(f"{t['name']} by {', '.join(a['name'] for a in t['artists'])} - {t['uri']}" for t in tracks)


@mcp.tool
def play_song(ctx: Context, uri: str, device_id: str = None) -> str:
    """Plays a song on the specified device."""
    sp = get_spotify_client(ctx)
    sp.start_playback(device_id=device_id, uris=[uri])
    return f"Playing {uri}."


@mcp.tool
def stop_playback(ctx: Context, device_id: str = None) -> str:
    """Stops playback on the specified device."""
    sp = get_spotify_client(ctx)
    sp.pause_playback(device_id=device_id)
    return "Playback paused."


if __name__ == "__main__":
    mcp.run(transport="http")
