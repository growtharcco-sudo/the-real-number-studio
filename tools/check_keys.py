"""Check that the Instagram and YouTube keys work. Reads account info only; posts nothing."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "poster"))
import requests
ok = True
tok, uid = os.environ.get("IG_TOKEN", ""), os.environ.get("IG_USER_ID", "")
if not tok or not uid:
    print("Instagram: IG_TOKEN or IG_USER_ID is missing"); ok = False
else:
    if not uid.isdigit(): print("Instagram: IG_USER_ID should be only digits (17841412838217113)"); ok = False
    import instagram
    base = instagram._base(tok)
    r = requests.get(f"{base}/{uid}", params={"fields": "username", "access_token": tok}, timeout=30)
    print("Instagram:", "OK, connected to @" + r.json().get("username", "?") if r.ok else f"FAILED {r.status_code} {r.text[:300]}")
    ok &= r.ok
    if r.ok:
        r = requests.get(f"{base}/{uid}/content_publishing_limit", params={"fields": "quota_usage,config", "access_token": tok}, timeout=30)
        print("Instagram publishing quota:", r.json() if r.ok else f"could not read ({r.status_code})")
        if tok.startswith("EAA"):
            import datetime as _dt
            d = requests.get("https://graph.facebook.com/debug_token", params={"input_token": tok, "access_token": tok}, timeout=30)
            if d.ok:
                j = d.json().get("data", {}); exp = j.get("expires_at", None); dexp = j.get("data_access_expires_at", None)
                f = lambda t: "NEVER" if t in (0, None) else _dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
                print("Instagram token type:", j.get("type"), "| valid:", j.get("is_valid"), "| expires:", f(exp), "| data access expires:", f(dexp))
            else:
                print("Instagram token expiry: could not read", d.status_code, d.text[:200])
        else:
            print("Instagram token: Instagram-login type (60-day, needs refresh)")
if os.environ.get("YT_REFRESH_TOKEN"):
    try:
        import youtube
        from googleapiclient.errors import HttpError
        yt = youtube._client()
        print("YouTube: OK, token accepted (upload scope only, so channel name isn't readable)")
        yt._http.credentials.refresh(__import__("google.auth.transport.requests", fromlist=["Request"]).Request())
    except Exception as e:
        print("YouTube: FAILED", e); ok = False
else:
    print("YouTube: not set up yet")
sys.exit(0 if ok else 1)
