import sys, urllib, sentiment, json, time
import optparse

import tweepy
import json

from secrets import *

def get_client_access():
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)    
    api = tweepy.API(auth)
    # Twitter desktop OAuth for client accounts
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        print("Error! Failed to get request token.")
    
    print(redirect_url)
    
    verifier = input('Verifier:')
    
    try:
        auth.get_access_token(str(verifier))
    except tweepy.TweepError as e:
        print("Error! Failed to get access token.", e)
    
    new_token = auth.access_token
    print "Access token:", new_token
    new_secret = auth.access_token_secret
    print "Access token secret:", new_secret
    
    auth.set_access_token(new_token, new_secret)
    return api

        
##override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        print(status.text)
        try: 
            words = status.text.split(' ')
            tweetId = status.id_str
            requester = status.user.screen_name
            users = []
            for w in words: 
                if w[:1] == "@" and w[1:] != "howrufeelingbot":
                    users.append(w[1:])
            print "On status users", users
            process_users(users, tweetId, requester)
            # with open('tweet.tmp', 'w') as f:
            #     f.write(users)
        except Exception as e:
            print "Error occured while parsing tweet", e
    
def process_users(users, tweetId, requester):
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)    
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    try: 
        if users:
            print "Got tweet! Users they want me to analyze:", users
            for user in users:
                analyze_sentiment(user, api, tweetId, requester)   
        else: 
            print "Got tweet, no users to analyze though. :("
    except Exception as e:
        print "Error: ", e
        
def analyze_sentiment(user, api, tweetId, requester):
    try:
        print "Searching tweets for: %s." % user
        tweets = []
        for res in api.user_timeline(screen_name = user, count = 100, include_rts = True):
            tweets.append(res.text)
            
        c = sentiment.Classifier()
        results = c.classify(tweets)
        positive = [result for result in results if result['classification'] == 'pos']
        negative = [result for result in results if result['classification'] == 'neg']
        for result in results:
            if result['classification'] == 'pos':
                print "Good: %s\n" % result['content']
            else:
                print "Bad: %s\n" % result['content']
        unknown = len(tweets) - len(results)
        
        out = "Tweets analyzed: %d | Positive: %d | Negative: %d | Unknown: %s" % (len(tweets), len(positive), len(negative), unknown)
        pos_percent = float(len(positive))/float(len(results))*100
        neg_percent = float(len(negative))/float(len(results))*100
        metrics = "Percentiles - Positive: %d%%, Negative: %d%%" % (pos_percent, neg_percent)
        
        print "="*84
        print "= %s =" % out.center(80)
        print "= %s =" % metrics.center(80)
        print "="*84
        
        tweet_result(user, len(tweets), len(positive), len(negative), unknown, pos_percent, neg_percent, tweetId, requester)
                    
    except Exception as e:
        print "Sorry, couldn't analyze tweets for %s!" % user
        print "Error:", e

def tweet_result(user, num_tweets, positive, negative, unknown, pos_percent, neg_percent, tweetId, requester):
    result = "@{7} I analyzed {0} of @{1}'s tweets. Here are the results: {2} positive, {3} negative, {4} unknown. Overall, {5}% are positive and {6}% are negative!".format(num_tweets, user, positive, negative, unknown, pos_percent, neg_percent, requester)
    print "Tweet id to reply to:", tweetId
    try: 
        api.update_status(result, in_reply_to_status_id=tweetId)
    except Exception as e:
        print "Tweeting result failed:", e
                    

if __name__ == "__main__":
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)    
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    
    StreamListener = MyStreamListener()
    stream = tweepy.Stream(auth = api.auth, listener=StreamListener)
    
    try:
        stream.filter(track=['howrufeelingbot'])
    except KeyboardInterrupt:
        stream.disconnect()
        print " Keyboard Interrupt: Stopped stream"

    
    
