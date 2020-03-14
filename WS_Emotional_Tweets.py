# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 14:52:00 2020

@author: lewis
"""
import pandas as pd
import tweepy
from pymongo import MongoClient
import re
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
#nltk.download("vader_lexicon")


# # # TWITTER CREDENTIALS # # #
ACCESS_TOKEN = "2343367800-Y9AgcsBAV18X1NgFpdhpYFEkWg1iKMhY2pf6kit"
ACCESS_TOKEN_SECRET = "KjlZY07yvUbtyEYJjzAQ4jwOAe07cEO0xSkwr9POq5KPN"
CONSUMER_KEY = "P2dk1LqFch4Zl3hcbokCyH8xY"
CONSUMER_SECRET = "jwjPJOdjxkdJFvl3PwNfuVn9UaqQflAjcHvh6S7vq8LuD065z0"

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

 
         # # # EMOTIONS # # #
#+ve         
happy = ["#happy", "#joy","#love","😂"]  
exciting = ["#exciting","#thrill","#amazing","🔥"]     
surprise = ["#wow","#surpise","#surprised","#shocked","😮"]
#-ve
sad = ["#sad","#crying","#depressed","😭","😢"] 
fear = ["#fear","#scary","#anxiety","😱"]
angry= ["#angry","#hate","#rage","#mad","😡"] 


# # # CLEANER # # #
class Cleaner(object):  
    def __init__(self):    
        self.repeat_regexp = re.compile(r'(\w*)(\w)\2(\w*)')
        self.repl = r"\1\2\3" 
  
#removes repeated letters from words      
    def replace(self, word): 
        #checks dictionary for words so as not to remove words that 
        #are supposed to have repeated letters
        if wordnet.synsets(word):      
            return word         
        repl_word = self.repeat_regexp.sub(self.repl, word)
        if repl_word != word:      
            return self.replace(repl_word)    
        else:      
            return repl_word
  
#applies the replace function to an entire sentance      
    def full_replace(self,text): 
        clean = Cleaner()
        text = word_tokenize(text) #splits sentance into words
        word = [clean.replace(t) for t in text] #applies replace to each words
        parse=" "
        text = parse.join(word) #rejoins sentance
        return text
       
    def clean(self,text):
        text = re.sub(r'@[A-Za-z0-9]+','',text) #removes mentions
        #removes underscores as sometimes they are contained within handles
        #and the previous line does not remove the entire handle
        text = re.sub(r'_[A-Za-z0-9]+','',text)       
        text = re.sub('https?://[A-Za-z0-9./]+','',text) #removes links
        text = text.split() #seperates sentance into words
        while text[-1].startswith("#"): #removes tail hashtags
            text = text[:(-1)]
        if text[0] == "RT": #removes "RT" from start of tweets which are retweets
            text = text[1:]
        if text[0] == ":": #removes colons at the start of tweets which appear
            text = text[1:]#when tweet is a retweet
        parse = " "
        text = parse.join(text)
        return text

def full_clean(text): #applies all cleaning functions at once
    text=Cleaner.clean(Cleaner,text)
    text=Cleaner.full_replace(Cleaner,text)
    return text

  
  
# # # COLLECT TWEETS # # #
print("running")

for w in happy: #selects each hashtag/emoticon in happy list indvidually
    #collects a set number of english tweets
    emo = tweepy.Cursor(api.search,q=w,tweet_mode="extended",lang="en",encoding="utf-8-sig").items(200)
    client = MongoClient("localhost",27017) #connects to the database
    db=client.tweet_db
    for t in emo: #selects each tweet individually
        text=t._json #converts to json
        db.happy.insert_one(text) #inserts into the collection named happy

#collects the tweets from Mongodb database and inserts them into a dataframe        
hpdf = pd.DataFrame(list(db.happy.find())) 
#apply cleaning function to each row
hpdf["full_text"]=hpdf["full_text"].apply(full_clean) 
hpdf = hpdf.drop_duplicates(subset="full_text") #remove duplicate tweets

#determine sentiment score
hpe = [] #create empty list
for t in hpdf["full_text"]: #selects the text of each tweet individually
    sid = SentimentIntensityAnalyzer()
    #determine which tweets have sentiment score greater than 0.5
    e = sid.polarity_scores(t)["compound"]>0.5
    hpe.append(e) #result to list
#add "tweet sentiment score row > 0.5" column to database   
hpdf["score"] = hpe 

print("happy:")
#print number of tweets in dataframe to check 150 minimum has been met
print(len(hpdf.index)) 
#print number of tweets with sentiment score > 0.5 in dataframe
print(len(hpdf[hpdf.score == True].index))
        
for w in exciting:    
    emo = tweepy.Cursor(api.search,q=w,tweet_mode="extended",lang="en",encoding="utf-8-sig").items(200)
    client = MongoClient("localhost",27017)
    db=client.tweet_db
    for t in emo:
        text=t._json
        db.exciting.insert_one(text)
        
exdf = pd.DataFrame(list(db.exciting.find()))
exdf["full_text"]=exdf["full_text"].apply(full_clean)
exdf = exdf.drop_duplicates(subset="full_text")

exe = []
for t in exdf["full_text"]:
    sid = SentimentIntensityAnalyzer()
    e = sid.polarity_scores(t)["compound"]>0.5
    exe.append(e)
exdf["score"] = exe
print("exciting:")
print(len(exdf.index))
print(len(exdf[exdf.score == True].index))
        
for w in surprise:    
    emo = tweepy.Cursor(api.search,q=w,tweet_mode="extended",lang="en",encoding="utf-8-sig").items(300)
    client = MongoClient("localhost",27017)
    db=client.tweet_db
    for t in emo:
        text=t._json
        db.surprise.insert_one(text)
        
spdf = pd.DataFrame(list(db.surprise.find()))
spdf["full_text"]=spdf["full_text"].apply(full_clean)
spdf = spdf.drop_duplicates(subset="full_text")
spe = []
for t in spdf["full_text"]:
    sid = SentimentIntensityAnalyzer()
    e = sid.polarity_scores(t)["compound"]>0.5
    spe.append(e)
spdf["score"] = spe
print("surprise:")
print(len(spdf.index))
print(len(spdf[spdf.score == True].index))

        
for w in sad:    
    emo = tweepy.Cursor(api.search,q=w,tweet_mode="extended",lang="en",encoding="utf-8-sig").items(200)
    client = MongoClient("localhost",27017)
    db=client.tweet_db
    for t in emo:
        text=t._json
        db.sad.insert_one(text)
        
sddf = pd.DataFrame(list(db.sad.find()))
sddf["full_text"]=sddf["full_text"].apply(full_clean)
sddf = sddf.drop_duplicates(subset="full_text")
sde = []
for t in sddf["full_text"]:
    sid = SentimentIntensityAnalyzer()
    e = sid.polarity_scores(t)["compound"]<-0.5
    sde.append(e)
sddf["score"] = sde

print("sad:")
print(len(sddf.index))
print(len(sddf[sddf.score == True].index))
        
for w in fear:    
    emo = tweepy.Cursor(api.search,q=w,tweet_mode="extended",lang="en",encoding="utf-8-sig").items(200)
    client = MongoClient("localhost",27017)
    db=client.tweet_db
    for t in emo:
        text=t._json
        db.fear.insert_one(text)
        
frdf = pd.DataFrame(list(db.fear.find()))
frdf["full_text"]=frdf["full_text"].apply(full_clean)
frdf = frdf.drop_duplicates(subset="full_text")
fre = []
for t in frdf["full_text"]:
    sid = SentimentIntensityAnalyzer()
    e = sid.polarity_scores(t)["compound"]<-0.5
    fre.append(e)
frdf["score"] = fre
print("fear:")
print(len(frdf.index))
print(len(frdf[frdf.score == True].index))
        
for w in angry:    
    emo = tweepy.Cursor(api.search,q=w,tweet_mode="extended",lang="en",encoding="utf-8-sig").items(150)
    client = MongoClient("localhost",27017)
    db=client.tweet_db
    for t in emo:
        text=t._json
        db.angry.insert_one(text)

andf = pd.DataFrame(list(db.angry.find()))
andf["full_text"]=andf["full_text"].apply(full_clean)
andf = andf.drop_duplicates(subset="full_text")
ane = []
for t in andf["full_text"]:
    sid = SentimentIntensityAnalyzer()
    e = sid.polarity_scores(t)["compound"]<-0.5
    ane.append(e)
andf["score"] = ane
print("angry:")
print(len(andf.index))
print(len(andf[andf.score == True].index))

emo_cols = ["id","created_at","full_text"] #select colums for csv file

#create csv file with selected columns for tweets in dataframe 
hpdf.to_csv (r'Emotions\happy.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")

exdf.to_csv (r'Emotions\exciting.csv', index = False, header=True, columns=emo_cols,encoding="utf-8-sig")
spdf.to_csv (r'Emotions\surprise.csv', index = False, header=True, columns=emo_cols,encoding="utf-8-sig")
sddf.to_csv (r'Emotions\sad.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")
frdf.to_csv (r'Emotions\fear.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")
andf.to_csv (r'Emotions\angry.csv', index = False, header=True ,columns=emo_cols, encoding="utf-8-sig")

#select 50 "emotionally charged" tweets from dataframe for sample 
hp_sample = hpdf.sort_values(by=["score"], ascending=False).head(50)
#create csv file of sample tweets
hp_sample.to_csv (r'Emotions\happy_sample.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")

ex_sample = exdf.sort_values(by=["score"], ascending=False).head(50)
ex_sample.to_csv (r'Emotions\exciting_sample.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")
sp_sample = spdf.sort_values(by=["score"], ascending=False).head(50)
sp_sample.to_csv (r'Emotions\surprise_sample.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")
sd_sample = sddf.sort_values(by=["score"], ascending=False).head(50)
sd_sample.to_csv (r'Emotions\sad_sample.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")
fr_sample = frdf.sort_values(by=["score"], ascending=False).head(50)
fr_sample.to_csv (r'Emotions\fear_sample.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")
an_sample = andf.sort_values(by=["score"], ascending=False).head(50)
an_sample.to_csv (r'Emotions\angry_sample.csv', index = False, header=True, columns=emo_cols, encoding="utf-8-sig")

print("done")
    


