# twitter_stream_statuses.py
Python 2 command line script to stream tweets from specified user ids

## Dependencies

Written for python2, pip install the single dep:

* [tweepy](https://github.com/tweepy/tweepy)

## Usage

The script will print URLs to stdout. If you want to pipe that to netcat, [irccat](https://github.com/irccloud/irccat) or whatever else, make sure you run python in unbuffered `-u` mode, e.g.:

```bash
python2 -u twitter_stream_statuses.py \
    --consumer_key=TWITTER_CONSUMER_KEY \
    --consumer_secret=TWITTER_CONSUMER_SECRET \
    --access_token=TWITTER_ACCESS_TOKEN \
    --access_token_secret=TWITTER_ACCESS_TOKEN_SECRET \
    --user_ids=USER_IDS |
    while IFS= read -r line
    do
        echo "#channel $line" |
            nc -q0 irccat.host 12345
    done
````

## Contributing

The above example runs continually as a service. Modifying it for use as a library in other software or upgrading it to python3 would be welcome contributions.
