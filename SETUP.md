# One-time setup (about 30 minutes)

Everything is free. Your keys go only into GitHub's encrypted Secrets, never into a file or a chat.

## A. GitHub repository
1. github.com → **+** → **New repository** → name `the-real-number-studio` → **Public** → Create.
   (Public is what makes GitHub Pages and Actions free. Keys stay secret; queued videos are reachable
   only by their exact link for a few hours before they post.)
2. Tell Claude "repo created". Claude pushes the code and the first video.
3. Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `media` / `(root)` → Save.

## B. Instagram key (Meta system-user token, never expires)
`IG_TOKEN` is a **system-user token** from Meta Business settings. It never expires, so there is
no refresh job. Do not switch back to the 60-day "Instagram login" key.

How it is set up (done 4 Nov 2026):
- Business portfolio **The Real Number**, with the Facebook Page **The Real Number** linked to `@the_real.number`.
- System user **unhyped-poster** (Admin), with **Full control** over the Page, `@the_real.number`
  and the app **Real Number Studio**.
- Token settings: app **Real Number Studio**, expiration **Never**, permissions
  `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
- `IG_USER_ID` is the Instagram account ID `17841412838217113` (unchanged).

If the key ever has to be replaced:
1. business.facebook.com → **Settings → Users → System users → unhyped-poster → Generate token**.
2. Pick the same app, expiration **Never**, and the same four permissions. Copy the token.
3. Repo → **Settings → Secrets and variables → Actions** → update `IG_TOKEN`. Never paste it into a chat.
4. Repo → **Actions → Check keys (posts nothing) → Run workflow**. It should print `SYSTEM_USER | valid: True | expires: NEVER`.

Warning: **unhyped-poster is shared with the tech channel The Unhyped.** Revoking its tokens or
removing that system user stops posting on **both** channels.

## C. YouTube key (Google Cloud)
1. console.cloud.google.com → **New project** `the-real-number`.
2. **APIs & Services → Library** → **YouTube Data API v3** → Enable.
3. **OAuth consent screen** → External → app name `The Real Number Studio`, your email → add scope
   `.../auth/youtube.upload` → then **Publish app** (status "In production").
   Important: in "Testing" mode the key dies after 7 days.
4. **Credentials → Create credentials → OAuth client ID → Desktop app** → Download JSON.
5. On your Mac, in Terminal:
   ```
   git clone https://github.com/growtharcco-sudo/the-real-number-studio && cd the-real-number-studio
   pip3 install google-auth-oauthlib
   python3 tools/get_youtube_token.py ~/Downloads/client_secret_XXXX.json
   ```
   Sign in with the Google account that owns @Thereal.number. Click *Advanced → Go to app* on the
   "unverified" warning (it's your own app). It prints three values: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
6. Apply for the free audit so uploads can be public: https://support.google.com/youtube/contact/yt_api_form
   Until it is approved, YouTube keeps API uploads **private**: open YouTube Studio and switch each Short to Public.

## D. Paste the secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**, one each:
`IG_USER_ID`, `IG_TOKEN`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
(No `GH_PAT` is needed any more: nothing refreshes the Instagram key. If an old `GH_PAT` secret is there, it can be deleted.)

## E. Test
Repo → **Actions → Post due Reels → Run workflow**. A green tick means it worked.
If a post ever fails, GitHub emails you, and the error is saved in `queue/<id>/result.json`.
