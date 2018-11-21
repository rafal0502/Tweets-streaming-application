import sys
from textblob import TextBlob

for line in sys.stdin:
    try:
        line = line.strip()
        user_screenname, text, unix_time = line.split("\t")
        analysis = TextBlob(text)
        sentiment = analysis.sentiment.polarity
        print (user_screenname,text,sentiment)
    except:
        pass