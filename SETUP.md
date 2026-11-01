# One-time setup (about 30 minutes)

Everything is free. Your keys go only into GitHub's encrypted Secrets, never into a file or a chat.

## A. GitHub repository
1. github.com → **+** → **New repository** → name `the-real-number-studio` → **Public** → Create.
   (Public is what makes GitHub Pages and Actions free. Keys stay secret; queued videos are reachable
   only by their exact link for a few hours before they post.)
2. Tell Claude "repo created". Claude pushes the code and the first video.
3. Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch: `media` / `(root)` → Save.

## B. Instagram key (Meta developer app)
1. developers.facebook.com → **My Apps → Create app** → use case **"Manage messaging & content on Instagram"**.
2. In the app: **Instagram → API setup with Instagram login** → **Add account** → log in as `@the_real.number`.
3. Next to the account, click **Generate token**. Copy it. That is `IG_TOKEN` (valid 60 days; the workflow refreshes it every Monday).
4. The number shown next to the account is `IG_USER_ID`.
5. Leave the app in **Development** mode. It only needs to post to your own account.

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

## D. GitHub token for the weekly Instagram key refresh
github.com → Settings → Developer settings → **Fine-grained tokens** → Generate →
Repository access: only `the-real-number-studio` → Permissions: **Secrets: Read and write** → Generate.
That is `GH_PAT`.

## E. Paste the secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**, one each:
`IG_USER_ID`, `IG_TOKEN`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `GH_PAT`.

## F. Test
Repo → **Actions → Post due Reels → Run workflow**. A green tick means it worked.
If a post ever fails, GitHub emails you, and the error is saved in `queue/<id>/result.json`.
