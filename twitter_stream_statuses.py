#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, print_function

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import json
import logging
import argparse


# Debugging for all imports
# logging.basicConfig(level=logging.DEBUG)

# create logger
logger = logging.getLogger('twitter_stream')
logger.setLevel(logging.INFO)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)


argparser = argparse.ArgumentParser(
    description='Print tweets from selected users, excluding replies'
)
argparser.add_argument(
    '--consumer_key', help='Twitter API consumer key',
    required=True
)
argparser.add_argument(
    '--consumer_secret', help='Twitter API consumer secret',
    required=True
)
argparser.add_argument(
    '--access_token', help='Twitter API access token',
    required=True
)
argparser.add_argument(
    '--access_token_secret', help='Twitter API access token secret',
    required=True
)
argparser.add_argument(
    '-u', '--user_ids', help='Twitter user ids to follow, comma separated',
    required=True
)
args = argparser.parse_args()

USER_IDS = args.user_ids.split(',')

def is_self_reply_to_other(message):
    if (
        'entities' in message
        and 'user_mentions' in message['entities']
        and len(message['entities']['user_mentions'])
    ):
        first_mention = message['entities']['user_mentions'][0]
        if (
            first_mention['indices'][0] == 0
            and first_mention['id_str'] not in USER_IDS
        ):
            return True
    return False

def expand_entities(message):
    text = message['text']
    indices = {}
    if 'entities' in message:
        for entity_type in ['media', 'urls']:
            if entity_type in message['entities']:
                for entity in message['entities'][entity_type]:
                    if 'indices' in entity:
                        indices[entity['indices'][0]] = entity
    end_index = 0
    expanded_parts = []
    for i, e in sorted(indices.items()):
        expanded_parts.append(text[end_index:i])
        expanded_parts.append(e['expanded_url'])
        end_index = e['indices'][1]
    expanded_parts.append(text[end_index:])
    return ''.join(expanded_parts)

def get_tweet_url(message):
    screen_name = message['user']['screen_name']
    return 'https://twitter.com/%s/status/%s' % (
        screen_name, message['id_str']
    )

def log_status(message):
    url = get_tweet_url(message)
    screen_name = message['user']['screen_name']
    prefix = '@%s: ' % screen_name
    logger.info(url)
    if 'retweeted_status' in message:
        logger.info('%sRT @%s: %s' % (
            prefix,
            message['retweeted_status']['user']['screen_name'],
            expand_entities(message['retweeted_status'])
        ))
    else:
        logger.info('%s%s' % (
            prefix,
            expand_entities(message)
        ))

class Listener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    def on_connect(self):
        logger.info('Connected')
    
    def on_data(self, data):
        try:
            message = json.loads(data)
        except Exception, e:
            logger.error('Invalid json: %s\n%s' % (e, data))
            return True
        
        try:
            if 'in_reply_to_status_id' in message:
                if message['user']['id_str'] in USER_IDS:
                    # Filter mentions from others
                    reply_to_uid = message['in_reply_to_user_id']
                    reply_to_id = message['in_reply_to_status_id']
                    if (
                        (reply_to_id or reply_to_uid) and
                        reply_to_uid != message['user']['id']
                    ):
                        logger.info('Filter non-self reply')
                        log_status(message)
                        return True
                    elif is_self_reply_to_other(message):
                        logger.info('Filter self reply to other')
                        log_status(message)
                        return True
                    log_status(message)
                    print(get_tweet_url(message))
            elif 'limit' in message:
                logger.warning('Limit: %s' % data)
            elif 'disconnect' in message:
                logger.warning('Disconnect: %s' % data)
            elif 'warning' in message:
                logger.warning('Warning: %s' % data)
        except:
            logger.exception('Data exception\n%s' % (data))
        return True
        
    def on_error(self, status):
        if status == 420:
            logger.warning('Rate limited')
        else:
            logger.warning('Error response: %s' % status)
    
    def on_exception(self, exception):
        logger.error('Stream exception: %s' % exception)

if __name__ == '__main__':
    l = Listener()
    
    auth = OAuthHandler(args.consumer_key, args.consumer_secret)
    auth.set_access_token(args.access_token, args.access_token_secret)

    stream = Stream(auth, l)
    logger.info('Following: %s' % USER_IDS)
    stream.filter(follow=USER_IDS)
