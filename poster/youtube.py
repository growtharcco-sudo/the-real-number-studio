"""Upload a Short with the official YouTube Data API v3.

Needs: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (scope youtube.upload).
Note: until Google audits the API project, YouTube forces API uploads to private.
"""
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def _client():
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token",
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_short(path, title, description, tags=None, privacy=None):
    privacy = privacy or os.environ.get("YT_PRIVACY", "public")
    body = {"snippet": {"title": title[:100], "description": description[:4900], "tags": tags or [],
                        "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True}}          # the "altered or synthetic content" disclosure
    yt = _client()
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(path, mimetype="video/mp4", resumable=True, chunksize=8 << 20))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return {"yt_video_id": resp["id"], "yt_url": f"https://youtube.com/shorts/{resp['id']}",
            "yt_privacy": resp.get("status", {}).get("privacyStatus")}


def set_thumbnail(video_id, image_path):
    """Try to set the cover as the Short's thumbnail. YouTube only accepts this for channels that have
    custom Shorts thumbnails (rolling out from July 2026, Partner Program first) and a phone-verified
    account. Never raises: returns {"yt_thumb": "set"} or {"yt_thumb": "not allowed: <reason>"}."""
    try:
        src = image_path
        if os.path.getsize(src) > 2_000_000:                   # API limit is 2 MB: high-quality JPEG copy
            from PIL import Image
            src = image_path.rsplit(".", 1)[0] + "_yt.jpg"
            Image.open(image_path).convert("RGB").save(src, "JPEG", quality=95)
        mime = "image/jpeg" if src.endswith(".jpg") else "image/png"
        _client().thumbnails().set(videoId=video_id, media_body=MediaFileUpload(src, mimetype=mime)).execute()
        return {"yt_thumb": "set"}
    except Exception as e:
        return {"yt_thumb": f"not allowed: {str(e)[:200]}"}
