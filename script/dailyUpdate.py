import os
import re
import time
from tqdm import tqdm
from datetime import datetime, timedelta
from pathlib import Path

import commentjson
from dotenv import load_dotenv
from lib import connectEndpoint, createTimelinesUrl, saveAsJSON

load_dotenv()  # take environment variables from `.env``

cwd = Path.cwd()
# 現時点からちょうど n 時間前の日付を取得
TIME_RANGE = int(os.environ.get("TIME_RANGE", 24 + 1))
START_TIME = datetime.now() + timedelta(hours=-TIME_RANGE)

# オプション設定
ENABLE_MENTION = bool({"t": 1, "true": 1, "f": 0, "false": 0}[os.environ.get("ENABLE_MENTION", "false")])

# 正規表現
pattern_user_id = re.compile(r"\d+")


def convertListToStr(list_):
    return ",".join(list_) if type(list_) is list else str(list_)


def getParams(pagination_token: str = None):
    filepath = cwd / "queryParameters.json"
    config = commentjson.loads(filepath.read_text())
    param_fields = [
        "expansions",
        "tweet.fields",
        "media.fields",
        "place.fields",
        "poll.fields",
    ]
    param_dict = {k: convertListToStr(v) for k, v in config.items() if k in param_fields}
    param_dict.update(
        {
            "max_results": 100,
            "start_time": START_TIME.isoformat(timespec="seconds") + "Z",
            "pagination_token": pagination_token,
        }
    )

    return param_dict


def procedure(user_id: int, endpoint="tweets", next_token=None):
    url = createTimelinesUrl(user_id, endpoint)
    params = getParams() if next_token is None else getParams(next_token)
    json_response = connectEndpoint(url, params)
    # print(json.dumps(json_response, indent=4, sort_keys=True, ensure_ascii=False))
    # TIME_RANGE の範囲ではツイートが見つけられなかった場合、response には `data` が含まれない
    if "data" not in json_response:
        return
    else:
        saveAsJSON(user_id, endpoint, json_response)

    if "meta" in json_response and "next_token" in json_response["meta"]:
        pagination_token = json_response["meta"]["next_token"]
        time.sleep(2)  # wait 2 seconds
        procedure(user_id, endpoint, pagination_token)

    return


def main():
    source = cwd / "targetList.txt"

    for id in source.read_text().split("\n"):
        print(id)

    target_id_list = [
        int(pattern_user_id.match(id)[0])
        for id in source.read_text().split("\n")
        if len(id) > 0 and pattern_user_id.match(id) is not None
    ]

    for user_id in tqdm(target_id_list):
        procedure(user_id)
        if ENABLE_MENTION:
            procedure(user_id, endpoint="mentions")

    return


if __name__ == "__main__":
    main()
