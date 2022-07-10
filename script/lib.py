# cf. https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/User-Tweet-Timeline/user_tweets.py

import os
import json
import collections

import requests

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # take environment variables from `.env``

cwd = Path.cwd()
DATA_DIR = cwd / "data"

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")


def createTimelinesUrl(user_id: int, endpoint: str = "tweets") -> str:
    return f"https://api.twitter.com/2/users/{user_id}/{endpoint}"


def bearerOAuth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    r.headers["User-Agent"] = "v2UserTweetsPython"
    return r


def connectEndpoint(url, params):
    response = requests.request("GET", url, auth=bearerOAuth, params=params)
    # print(response.status_code)
    if response.status_code != 200:
        raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
    return response.json()


def extractTweets(data):

    tweets = {}

    for tweet in data:
        timestamp = tweet["created_at"].split("T")[0]
        if timestamp not in tweets:
            tweets[timestamp] = [tweet]
        else:
            tweets[timestamp].append(tweet)

    return tweets


def getTweetObjById(data, id):

    for tweet in data:
        if tweet["id"] != id:
            continue
        else:
            return tweet
    return


def makeFilepath(user_id, dir_name, datestr):
    year, month, day = datestr.split("-")
    filepath = DATA_DIR / str(user_id) / dir_name / year / month / f"{day}.json"
    if not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
    return filepath


def mergeTweetData(user_id, dir_name, timestamp, tweets):
    year, month, day = timestamp.split("-")
    filepath = DATA_DIR / str(user_id) / dir_name / year / month / f"{day}.json"
    # 既存のファイルが有れば, tweets を更新する
    if filepath.exists():
        obj = json.loads(filepath.read_text())
        old_ids = {tweet["id"] for tweet in obj["data"]}
        new_ids = {tweet["id"] for tweet in tweets}
        # old 側にしかない id を残して、 obj から取ってくる
        legacy_ids = old_ids.difference(new_ids)
        tweets += [getTweetObjById(obj["data"], id_) for id_ in legacy_ids]
    return tweets


def uniqueObjects(listOfObject):

    try:
        return list({v["id"]: v for v in listOfObject}.values())
    except:
        return list({v["media_key"]: v for v in listOfObject}.values())


def mergeIncludes(obj, filepath):

    includes = {"media": [], "places": [], "polls": []}

    if "includes" in obj:
        includes.update(obj["includes"])

    if not filepath.exists():
        return includes

    old_obj = json.loads(filepath.read_text())
    merged = {k: uniqueObjects(v + includes[k]) for k, v in old_obj["includes"].items()}

    return merged


def labelMeta(tweets):

    ids = sorted([tweet["id"] for tweet in tweets])
    meta = {
        "oldest_id": int(ids[0]) if len(ids) > 0 else None,
        "newest_id": int(ids[-1]) if len(ids) > 0 else None,
        # "next_token": "xxxxxxxxxxxxxxxx",
        "result_count": len(tweets),
    }
    return meta


def flatten(list_):
    for el in list_:
        if isinstance(el, collections.abc.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def removeDuplicates(includes, tweets):

    attachments = [tweet["attachments"] for tweet in tweets if "attachments" in tweet]

    media_keys = flatten([attc["media_keys"] for attc in attachments if "media_keys" in attc])
    poll_ids = flatten([attc["poll_ids"] for attc in attachments if "poll_ids" in attc])
    place_ids = [tweet["geo"]["place_id"] for tweet in tweets if "geo" in tweet]

    return {
        "media": [m for m in includes["media"] if m["media_key"] in media_keys],
        "polls": [p for p in includes["polls"] if p["id"] in poll_ids],
        "places": [p for p in includes["places"] if p["id"] in place_ids],
    }


def saveAsJSON(user_id: int, dir_name: str, obj: dict):

    tweet_data = {
        timestamp: mergeTweetData(user_id, dir_name, timestamp, tweets)
        for timestamp, tweets in extractTweets(obj["data"]).items()
    }

    for timestamp, tweets in tweet_data.items():
        filepath = makeFilepath(user_id, dir_name, timestamp)
        includes = removeDuplicates(mergeIncludes(obj, filepath), tweets)
        meta = labelMeta(tweets)
        output = {"data": tweets, "includes": includes, "meta": meta}
        result = json.dumps(output, indent=4, sort_keys=True, ensure_ascii=False)
        filepath.write_text(result)

    return
