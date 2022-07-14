# SATwi: 察威

"S" and "A" tw

- **S** ... silent, secret, search, save or share
- **A** ... approach, acquisition, activity, archive or analyze

Without read or write code, you can retrieve information about the activities on Twitter of politicians, activists, and other accounts via [Twitter API](https://developer.twitter.com/en/docs/twitter-api).

Under [Twitter's terms and conditions](https://developer.twitter.com/en/developer-terms), it is a violation to be "public" data obtained via the API, but there is absolutely no problem with collecting the data out of the sight of others, in other words "private".

## How to get it

<details>
<summary>0. Prepare GitHub accounts</summary>

To create a repository on github, you must obtain a github account.

- [Sign up || GitHub](https://github.com/signup)

</details>

<details>
<summary>1. Get a Twitter API token</summary>

Similarly, to use the Twitter API, you must obtain a Twitter developer account.

cf. [Getting access to the Twitter API | Docs | Twitter Developer Platform](https://developer.twitter.com/en/docs/twitter-api/getting-started/getting-access-to-the-twitter-api)

After sign up for dev, **save your App's key and tokens and keep them secure**.
On `SATwi`, we only use [_App Access Token_](https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens) a.k.a. `BEARER_TOKEN`.

- [Sign up || Twitter Developer Platform](https://developer.twitter.com/en/portal/petition/essential/basic-info)

</details>

<details>
<summary>2. "Fork" this repository</summary>

You can "fork" this repository and directly divert the script.
However, GitHub actually does not allow you to make the [forked repository](https://docs.github.com/en/get-started/quickstart/fork-a-repo) _private_.
Therefore, we will "import" this repository instead.

cf. [Importing a repository with GitHub Importer - GitHub Docs](https://docs.github.com/en/get-started/importing-your-projects-to-github/importing-source-code-to-github/importing-a-repository-with-github-importer)

1. Click [**Import repository**]
2. Enter the following URL:

- `https://github.com/Ningensei848/SATwi`

3. Name your new repository
4. Make repository visibility private
5. Click [**Begin import**]

</details>

## Configuration

There are three items in SATwi that should be set.

- targets
- parameters
- schedule

### Targets

It is a list of the account ID from which you wish to retrieve tweets.
Following the example in [targetList.txt](./targetList.txt), please enter one ID per line.

**Only numbers are read**, subsequent strings are ignored.
You may want to comment out the screen name and display name so that they are easy for a third person to read, as shown below.

```txt:targetList.txt
1247032696586436609 # kishida230: 岸田文雄
903338594 # sugawitter: 菅義偉
468122115 # AbeShinzo: 安倍晋三
```

Note that we use the unique ID for that user, not the screen name or display name.
This is because an ID is immutable by the system, while a screen / display name can be changed at will by the user (i.e., uniqueness is more difficult to guarantee).

There are many ways to identify the ID of each user on the web.
Please find the method that works best for you.

### Parameters

They can be set to change the behavior of the script being executed.

You can enter multiple of these from the [Settings > secrets > actions] of the repository.

cf. [Encrypted secrets - GitHub Docs](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository)

See below for a list of parameters that can be set.

#### BEARER_TOKEN

_**required**_ : (string)

Assign the _App Access Token_ obtained from Twitter Developer to this param.

#### ENABLE_MENTION

_optional_ : (boolean)

If true, it collects not only tweets "from" the target(s), but also tweets "to" the target(s).

(Default is `false`)

#### ENABLE_LIKED_TWEETS

_optional_ : (boolean)

If true, collect the last 100 "liked" tweets.

(Default is `false`)

<details>
<summary>Tips: If you want to retrieve past likes more than hundred ...</summary>

Unlike [`/users/:id/tweets`](https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets), you can go back as far as the Tweet caps will allow, even to past Likes.
However, you can only request [up to 75 likes in 15 minutes](https://developer.twitter.com/en/docs/twitter-api/tweets/likes/api-reference/get-users-id-liked_tweets) (= 7500 likes).
In other words, it is theoretically possible to get all the likes, but it is not practical to do so with GitHub Actions.
Instead, we are preparing a dedicated Jupyter Notebook on Google Colaboratory (coming soon !).

</details>

#### TIME_RANGE

_optional_ : (integer)

If specified, determines how many hours of tweets to retrieve retroactively.
Note that this param is limited to two digits because of the convenience of the python library, [`datetime`](https://docs.python.org/3/library/datetime.html#timedelta-objects).

(Default is `25`)

**Combined with `crontab`, it offers greater value** (See the [best practice](#best-practice) for more information.).

### Schedule

Thanks to Github Actions, scripts can now be executed automatically and regularly, even without a computing environment at hand.
Among the event triggers provided by Github actions, the timing of execution can be controlled by devising a special notation, [POSIX `cron` syntax](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/crontab.html#tag_20_25_07), to be entered in the [`schedule`](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule).

Note that scheduled workflows run on the latest commit on the default or base branch.
In addition , **the shortest interval you can run scheduled workflows is once every 5 minutes**.

cf. [`on.schedule` || Workflow syntax for GitHub Actions - GitHub Docs](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onschedule)

<details>
<summary>Cron syntax</summary>

> Cron syntax has five fields separated by a space, and each field represents a unit of time.

```txt
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of the month (1 - 31)
│ │ │ ┌───────────── month (1 - 12 or JAN-DEC)
│ │ │ │ ┌───────────── day of the week (0 - 6 or SUN-SAT)
│ │ │ │ │
│ │ │ │ │
│ │ │ │ │
* * * * *
```

</details>

Example:

> ```yml
> on:
>   schedule:
>     # * is a special character in YAML so you have to quote this string
>     - cron:  '30 5,17 * * *'
> ```

cf. [Schedule || Events that trigger workflows - GitHub Docs](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

#### Manual execution

It can be executed manually at the push of a button without having to wait for a scheduled run.
We have already set it up, so you can try it out by referring to the following article:

- [Manually running a workflow - GitHub Docs](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow)

#### Best practice

At most, `TIME_RANGE` should be limited to **twice** the length of the interval set in `cron`.

If the execution timing set by `cron` and the `TIME_RANGE` defined by Parameter are well combined, data can be collected efficiently.
For example, if it is executed **once every 4 hours** (i.e., `cron: '0 */4 * * *'`) and tweets are retrieved as far back as **24 hours** (i.e., `TIME_RANGE=24`), it is a waste of 20 hours of extra tweets.

Since there is [a monthly limit on the number of tweets](https://developer.twitter.com/en/docs/twitter-api/tweet-caps) that can be retrieved by the Twitter API, it is important to reduce unnecessary requests as much as possible in order to avoid exceeding the limit.

On the other hand, sometimes we are unlucky and the servers that GitHub and Twitter have are not in good shape.
The execution at that time will fail, and it will be one more cycle before the data is collected again.
In other words, you may miss some data!

Therefore we recommend to try **to retrieve tweets retroactively for two cycles each time** in anticipation of an occasional one-time error.

<details>
<summary>Alternatively,</summary>

If you are a LINE user, you can register with [LINE Notify](https://notify-bot.line.me) and set up the service to send notifications in case of failure, setting `LINE_ACCESS_TOKEN` in the parameter.

Please let us know in [the Issue](https://github.com/Ningensei848/SATwi/issues) if you have any wishes for integration with other notification services.

</details>

## Memo

<details>
<summary>Task list (only in Japanese)</summary>

### WIP

- [ ] 画像つきのツイートを行なった時、画像+本文でLINEに通知する
- [ ] もっと実行頻度を上げたい人のための Tips を用意
- [ ] 画像や動画等も抜いてきて保存する

### TODO

- [ ] RT したツイートは収集しない (exclude tweets)
- [ ] ID だけを抜き出した一覧ファイルを作り、再配布可能にする
- [ ] 集めたツイートを規約に沿って公開できるサイト
- [ ] 削除済みのツイを一覧で見る

#### via Jupyter notebook on Colab

- [ ] 過去 3200 件分のツイートも取得する
- [ ] Follow 一覧を取得する
- [ ] Follower 一覧を取得する
- [ ] OAuth 1.0a に対応する

#### Done

- [x] 過去 24 時間に投稿されたツイートを収集し、日毎にファイルを分けて保存する
- [x] 指定した時間ごとに定期実行する via GitHub Actions
- [x] いいね欄のツイートも別途保管する
- [x] 失敗時に LINE 通知する
- [x] **対象に対してメンションされたツイート**も収集し、日毎にファイルを分けて保存する

</details>

## Author

[![Twitter is what's happening in the world and what people are talking about right now.](https://img.shields.io/badge/@Ningensei848-%231DA1F2.svg?&style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/Ningensei848)

[![gmail](https://img.shields.io/badge/k.kubokawa@klis.tsukuba.ac.jp-%23757575.svg?&style=for-the-badge&logo=gmail&logoColor=EA4335)](mailto:k.kubokawa@klis.tsukuba.ac.jp)

## License

_This software is released under the [MIT License](LICENSE)._
