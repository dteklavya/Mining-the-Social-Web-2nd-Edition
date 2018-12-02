import json
from flask import Flask, request, redirect
import multiprocessing
from threading import Timer

import twitter
from twitter.oauth_dance import parse_oauth_tokens
from twitter.oauth import read_token_file, write_token_file

# Note: This code is exactly the flow presented in the _AppendixB notebook

OAUTH_FILE = "resources/ch09-twittercookbook/twitter_oauth"

# XXX: Go to http://twitter.com/apps/new to create an app and get values
# for these credentials that you'll need to provide in place of these
# empty string values that are defined as placeholders.
# See https://dev.twitter.com/docs/auth/oauth for more information 
# on Twitter's OAuth implementation, and ensure that *oauth_callback*
# is defined in your application settings as shown next if you are 
# using Flask in this IPython Notebook.

# Define a few variables that will bleed into the lexical scope of a couple of 
# functions that follow
# CONSUMER_KEY = ''
# CONSUMER_SECRET = ''

import configparser

config = configparser.ConfigParser()
config.read_file(open(r'./../twitter_keys'))


CONSUMER_KEY = config.get('T Section', 'CONSUMER_KEY')
CONSUMER_SECRET = config.get('T Section', 'CONSUMER_SECRET')


oauth_callback = 'http://127.0.0.1:5000/oauth_helper'
    
# Set up a callback handler for when Twitter redirects back to us after the user 
# authorizes the app

webserver = Flask("TwitterOAuth")
@webserver.route("/oauth_helper")
def oauth_helper():
    
    oauth_verifier = request.args.get('oauth_verifier')

    # Pick back up credentials from ipynb_oauth_dance
    oauth_token, oauth_token_secret = read_token_file(OAUTH_FILE)
    
    _twitter = twitter.Twitter(
        auth=twitter.OAuth(
            oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET),
        format='', api_version=None)
    
    oauth_token, oauth_token_secret = parse_oauth_tokens(
        _twitter.oauth.access_token(oauth_verifier=oauth_verifier, oauth_token=oauth_token, oauth_consumer_key=CONSUMER_KEY))

    # Write out the final credentials that can be picked up after the following
    write_token_file(OAUTH_FILE, oauth_token, oauth_token_secret)
    return "%s %s written to %s" % (oauth_token, oauth_token_secret, OAUTH_FILE)

# To handle Twitter's OAuth 1.0a implementation, we'll just need to implement a 
# custom "oauth dance" and will closely follow the pattern defined in 
# twitter.oauth_dance.

@webserver.route("/oauth_dance")
def oauth_dance():
    
    _twitter = twitter.Twitter(
        auth=twitter.OAuth('', '', CONSUMER_KEY, CONSUMER_SECRET),
        format='', api_version=None)

    oauth_token, oauth_token_secret = parse_oauth_tokens(
            _twitter.oauth.request_token(oauth_callback=oauth_callback))

    print(oauth_token, oauth_token_secret, "token and secret from twitter")
    # Need to write these interim values out to a file to pick up on the callback 
    # from Twitter that is handled by the web server in /oauth_helper
    write_token_file(OAUTH_FILE, oauth_token, oauth_token_secret)
    
    oauth_url = ('https://api.twitter.com/oauth/authorize?oauth_token=' + oauth_token)
    
    # Redirect to twitter URL for user authorization.
    return redirect(oauth_url, code=302)


@webserver.route("/trends/<int:woe_id>/")
def trends(woe_id):
    
    oauth_token, oauth_token_secret = read_token_file(OAUTH_FILE)
    
    auth = twitter.oauth.OAuth(oauth_token, oauth_token_secret,
                                   CONSUMER_KEY, CONSUMER_SECRET)
          
    twitter_api = twitter.Twitter(auth=auth)
    
    trends = twitter_api.trends.place(_id=woe_id)
#     print(json.dumps(trends, indent=1))

    return json.dumps(trends, indent=1)



webserver.run(host='0.0.0.0')

