# Get a repository info via GitHub API
# https://docs.github.com/ja/rest/repos/repos#get-a-repository

# curl \
#   -H "Accept: application/vnd.github+json" \
#   -H "Authorization: token <TOKEN>" \
#   https://api.github.com/repos/OWNER/REPO

import os
import json
import urllib.request


OWNER_AND_REPO = os.environ.get("OWNER_AND_REPO", "octocat/Hello-World")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)

url = f"https://api.github.com/repos/{OWNER_AND_REPO}"
req = urllib.request.Request(url)
req.headers = {"Accept": "application/vnd.github+json", "Authorization": f"token {GITHUB_TOKEN}"}

res = urllib.request.urlopen(req)
content = json.loads(res.read().decode("utf-8"))
print(str(content["private"]).lower())
