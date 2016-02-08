import csv
import random
import nltk

class Classifier(object):
    def __init__(self):
        print("Entering Test Data Reader")
        parsedTweets = self.read_tweets()

        print("Entering Classifier Trainer")
        self.classifier = nltk.NaiveBayesClassifier.train(parsedTweets)
        print("Exiting Classifier Trainer")

    def read_tweets(self):
        fp = open('sentiment.csv', 'r')
        reader = csv.reader(fp, delimiter=',', quotechar='"', escapechar='\\')
        tweets = []
        for row in reader:
            row = next(reader)
            split_words = [e.lower() for e in row[5].split() if len(e) >= 3]
            if(len(split_words)>0):
                tweets.append( ([e.lower() for e in row[5].split() if len(e) >= 3], row[0]))
        print("Entering Shuffle")
        random.shuffle(tweets)
        print("Exiting Shuffle")
        tweets = tweets[:100]		
        self.word_features = self.get_word_features(self.get_words_in_tweets(tweets))
        print("Features Extracted")
        training_set = nltk.classify.apply_features(self.extract_features, tweets)
        return training_set

    def classify(self, text):
        return self.classifier.classify(self.extract_features(text.split()))


    def get_words_in_tweets(self, tweets):
        all_words = []
        for i in range(0,len(tweets)):
            all_words = all_words + tweets[i][0]
        return all_words

    def get_word_features(self, wordlist):
        wordlist = nltk.FreqDist(wordlist)
        word_features = wordlist.keys()
        return word_features

    def extract_features(self, document):
        document_words = set(document)
        features = {}
        for word in self.word_features:
            features['contains(%s)' % word] = (word in document_words)
        return features
