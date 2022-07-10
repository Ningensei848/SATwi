# -*- coding: utf-8 -*-


# Commented out IPython magic to ensure Python compatibility.
# @title ライブラリのインストール via `pip`

# %pip install --upgrade pip
# %pip install --upgrade gspread python-dotenv requests
# %pip install requests-oauthlib tqdm

# @title 必要なライブラリ群をインポート

import re
import os
import json
import time
import pandas as pd
import datetime
import requests

from io import StringIO
from tqdm import tqdm
from dotenv import load_dotenv
from pathlib import Path
from dateutil import tz

# @title Colaboratory から spreadsheet を触れるように認証する
# cf. [Advanced Usage — gspread 5.3.2 documentation](https://docs.gspread.org/en/latest/advanced.html)
# --> full example: https://colab.research.google.com/notebooks/io.ipynb#scrollTo=sOm9PFrT8mGG

from google.colab import auth

auth.authenticate_user()

import gspread
from google.auth import default

creds, _ = default()

gc = gspread.authorize(creds)

# drive をマウントしてファイルに触れるようにする
from google.colab import drive

drive.mount("/content/drive")

# @title BEARER_TOKEN を準備 ※colab から入力する場合


CRED_FILENAME = "open-letters-research.cred"
filepath = Path(f"/content/drive/MyDrive/{CRED_FILENAME}")

# -----------------------------------------------------
# `BEARER_TOKEN` を入力する場合は以下 2 行をコメントアウトする
# BEARER_TOKEN = ""#@param {"type": "string"}
# filepath.write_text(f'BEARER_TOKEN="{BEARER_TOKEN}"')
# -----------------------------------------------------

print(filepath)
# print(filepath.read_text())

config = StringIO(filepath.read_text())
load_dotenv(stream=config)

# @title sheet の key を指定して CSV として読み出す

# NOTE: key の後、末尾に `/export?format=csv` とすることで、シートではなく生 CSV を渡すことができる
SHEET_KEY = "1-5KXy-o3e9JZhOSCwBPkA29Qng0UdLYrRRghzVxtjpY"  # @param {type:"string"}

df = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{SHEET_KEY}/export?format=csv", header=0)

"""## Twitter Dev API を利用してデータを得る

- [follows lookup](https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/Follows-Lookup/following_lookup.py)
  - `screen_name` ではなく、`user_id` が必要
  - 15 req / 15 min
- [get users with bearer token](https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/User-Lookup/get_users_with_bearer_token.py)
  - 900 req / 15 min

### 方針

- 何をするにも `user_id` が必要なので、先ずは `screen_name` から `user_id` を得るスクリプトを書く（シートにも追加する）
- すべての `user_id` が得られてから、適宜ループ処理を行なう
  - ただし、**Rate Limit** として「15 req/ 15 min」（1分あたり一回まで）という規制があるので、やりすぎないように留意する
  - 一回のリクエストで得られるフォロー数は最大で 1000 なので、それ以上フォローしている場合には複数回リクエストする必要がある
    - このため、 `user_id` の他に、事前にフォロー数/フォロワー数も持っておけると良さそう


"""

# @title BEARER_TOKEN を drive 内部のファイルから読み出す

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("BEARER_TOKEN")

print(bearer_token)

# @title サンプルコードを改変して調整
# cf. https://github.com/twitterdev/Twitter-API-v2-sample-code/blob/main/User-Lookup/get_users_with_bearer_token.py

TARGET_FIELDS = [
    "created_at",
    "description",
    "id",
    "location",
    "name",
    "profile_image_url",
    "protected",
    "public_metrics",
    # "url",  # bio 内のユーザ設定リンクが得られるが、短縮 URL なので不要
    "entities",
    "username",
]

# User fields are adjustable, options include:
# created_at, description, entities, id, location, name,
# pinned_tweet_id, profile_image_url, protected,
# public_metrics, url, username, verified, and withheld
user_fields = ",".join(TARGET_FIELDS)


def createUrl(usernames):
    url = f"https://api.twitter.com/2/users/by?usernames={usernames}&user.fields={user_fields}"

    return url


def bearerOAuth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserLookupPython"
    return r


def connectEndpoint(url):
    response = requests.request(
        "GET",
        url,
        auth=bearerOAuth,
    )
    # print(response.status_code)
    if response.status_code != 200:
        raise Exception("Request returned an error: {} {}".format(response.status_code, response.text))
    return response.json()


# @title 得られた JSON データから、短縮されていないされていない URL を得る


def getExpandedUrl(data):
    try:
        urls = data["entities"]["url"]["urls"]
        # entities.url 直下の `urls` は必ず一つなので、index は決め打ちで良い
        url = urls[0]["expanded_url"]
        return url
    except:
        return None


# @title ユーザごとのデータのうち、`entities` を `expanded_url` で置き換えて `website` とする


def replaceEntitiesInData(d):
    d["website"] = getExpandedUrl(d)

    if "entities" in d:
        del d["entities"]
    return d


# @title `public_metrics` がネストしているのでので Flatten する


def flattenPublicMetrics(d):

    for k, v in d["public_metrics"].items():
        d[k] = v

    del d["public_metrics"]

    return d


# @title 与えられた時刻情報文字列を JST に変更して返す

t_delta = datetime.timedelta(hours=+9)
JST = datetime.timezone(t_delta, "JST")


def convertTimeToJapanStandardTime(timestamp):
    # timestamp は "2016-03-19T16:14:23.000Z" といった形で与えられる
    dt_utc = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.000Z")
    dt_jst = dt_utc.astimezone(JST)
    return dt_jst.isoformat()


# sample_ts = "2016-03-19T16:14:23.000Z"
# dt = convertTimeToJapanStandardTime(sample_ts)

# print(type(dt), dt)

# @title 与えられた辞書に対して、`timestamp` という要素を追加する


def addTimestamp(d, timestamp):
    d["timestamp"] = timestamp
    d["created_at"] = convertTimeToJapanStandardTime(d["created_at"])

    return d


# @title `screen_name` のリストを渡すとユーザごとの情報を返す関数


def getUserData(name_list):
    sizeOfList = len(name_list)
    if sizeOfList < 1 or 100 < sizeOfList:
        raise Exception(
            f"The maximum size of the list passed to func `getUserData()` is 100 (in this case {sizeOfList} was passed)"
        )

    url = createUrl(usernames=",".join(name_list))
    json_response = connectEndpoint(url)

    timestamp = datetime.datetime.now()
    # e.g. 2016-03-19T16:14:23.000Z
    timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    timestamp = convertTimeToJapanStandardTime(timestamp)

    # `entities` から `expanded_url` を引っこ抜いて置き換える
    data = [replaceEntitiesInData(d) for d in json_response["data"]]
    # `public_metrics` がネストしているのでので Flatten する
    data = [flattenPublicMetrics(d) for d in data]
    # `timestamp` を追加する
    data = [addTimestamp(d, timestamp) for d in data]

    return data


# @title `twitter_id` 以外で得られる username の一覧を `memo` から取得する

pattern_screen_name = re.compile(r"@\w+")  # a-z, A-Z, 0-9, _


def getExtraScreenNames(dataframe):

    extra_usernames = []

    for cell in dataframe["memo"]:
        if pd.isna(cell):
            continue
        else:
            extra_usernames.extend(pattern_screen_name.findall(cell))
    # "@" を削除
    extra_usernames = [uname[1:] for uname in extra_usernames]
    return extra_usernames


# @title DataFrame から username を抜き出してリストにする

# df["twitter_id"] からすべてのすべての ID を取り出し、、100 ずつ回してデータを得る
# df["memo"] にもにも ID 情報が含まれるため、それも正規表現で抜き出す


def getUsernames():
    username_list = [id_ for id_ in df["twitter_id"] if not pd.isna(id_)]
    username_list.extend(getExtraScreenNames(df))
    username_list = [x.strip() for x in username_list]
    username_list = sorted(list(set(username_list)))

    return username_list


# @title `result` というリストを得る
username_list = getUsernames()

target_size = len(username_list)
print(f"Target size is {target_size}; Exec 100 pieces at a time.")

n = 100
result = []

for i in tqdm(range(0, len(username_list), n)):
    data = getUserData(username_list[i : i + n])
    # print(json.dumps(data, indent=4, sort_keys=True))
    time.sleep(2)  # サーバへの負荷軽減のためのため wait
    result.extend(data)

"""## データをシートに出力する

ここまでで `result` というリストを得た

この一つ一つの要素が、各ユーザの表面的な公開情報を含む辞書オブジェクトである

これを、df に変換した後にスプレッドシートに出力する


"""

# @title `result` は 「辞書オブジェクトのリスト」であるから、df へそのまま変換する

UNIQUE_KEY = "username"
df_result = pd.DataFrame(result)

# UNIQUE_KEY 以外のカラム名のリストを取得
current_cols = list(df_result.columns.values)
current_cols.remove(UNIQUE_KEY)

# UNIQUE_KEY が先頭に来るように再度カラムのリストを得る
new_cols = [UNIQUE_KEY]
new_cols.extend(current_cols)

# 列を入れ替える
df_result = df_result.reindex(columns=new_cols)

# NaN を含んだままだと、シートに出力する際に
# "Out of range float values are not JSON compliant"
# と怒られるので、NaN は取り除いて空白セルとする
df_result.fillna("", inplace=True)

df_result

# @title Spreadsheet を開き、書き込む

sh = gc.open_by_key(SHEET_KEY)
worksheet_list = sh.worksheets()
print(worksheet_list)

worksheet = sh.worksheet("twitter_accounts")

rows = [df_result.columns.values.tolist()] + df_result.values.tolist()
worksheet.update(rows)

# @title `account_list.tsv` としてファイル出力　→ username+id を他のスクリプトで活用

df_export = df_result.loc[:, ["username", "id"]]
df_export = df_export.assign(pagination_token=None, complete=False)


# カレントディレクトリにファイルとして出力
df_export.to_csv("account_list.tsv", sep="\t", index=False)

df_export
