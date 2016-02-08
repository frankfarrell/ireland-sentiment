ireland-sentiment
=================

Sentiment and Analysis for Irish Data Stream

# Prerequisites: 

* Erlang
 
* RabbitMQ
* Python 3+
* Run setup.sh -> installs needed python dependencies

* Get the training data produced here : http://help.sentiment140.com/for-students/
  Extract and rename file main sentiment.csv

# To Run: 

python tornadoapp.py
This trains a model a subscribes to rabbitmq channel

python: 

# Server-Side Stack 

Tornado
Nltk
Pika twitter client

# Client

Leaflet Map
d3js overlay showing Voronoi tessalation based on tweet sentiment

Code Description 
client.py: A message comes in, it is classified and pushed to all listeners
feed_producer.py : Sets up connection to twitter feed and pushes to queue
handlers.py : Accepts event listeners from clients
tornadoapp.py : Starts tornado application
tweetclassifier.py: sets up Naive Bayes Model based on historic twitter feed

