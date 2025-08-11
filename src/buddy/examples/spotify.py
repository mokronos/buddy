import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# --- AUTH ---
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))


def list_devices():
    devices = sp.devices()
    if not devices["devices"]:
        return "No active Spotify devices found."
    result = []
    for d in devices["devices"]:
        result.append(f"{d['name']} ({d['type']}) - ID: {d['id']}")
    return "\n".join(result)


def search_song(query, limit=5):
    results = sp.search(q=query, type="track", limit=limit)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return "No songs found."
    output = []
    for t in tracks:
        name = t["name"]
        artist = ", ".join(a["name"] for a in t["artists"])
        uri = t["uri"]
        output.append(f"{name} by {artist} - {uri}")
    return "\n".join(output)


def play_song(uri, device_id=None):
    try:
        sp.start_playback(device_id=device_id, uris=[uri])
        return f"Playing {uri}."
    except Exception as e:
        return f"Failed to play song: {e}"


def stop_playback(device_id=None):
    try:
        sp.pause_playback(device_id=device_id)
        return "Playback paused."
    except Exception as e:
        return f"Failed to pause playback: {e}"


# --- Example Usage ---
if __name__ == "__main__":
    print("Devices:\n", list_devices())
    print("\nSearch:\n", search_song("Daft Punk Get Lucky"))
    # play_song("spotify:track:69kOkLUCkxIZYexIgSG8rq")  # Example URI
    # stop_playback()
