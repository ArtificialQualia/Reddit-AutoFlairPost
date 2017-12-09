###
# This is where the magic happens.
#
# The important thing here is the decision to use DNNLinearCombinedClassifier
# Many classifiers were tried to fit the Reddit dataset on a number of subreddits
# None outperformed the built-in tensorflow DNNLinearCombinedClassifier
# Classifiers tried include (w/Keras and Tensorflow): Linear, built-in DNN, CNN, RNN
# A number of different loss functions, custom Estimators, and other custom settings
#  were tried, but I simply couldn't outperform default DNNLinearCombinedClassifier
#
# If you manage to get better generalized predictions from something else, please let me know!
###
import numpy as np
import pandas
import tensorflow as tf
import json
from random import randrange

class Model(object):
    
    def __init__(self, config, logger, modelLocation=None, *args, **kwargs):
        self.config = config
        self.logger = logger
        with open(self.config['Reddit.Subreddit']+'/RedditFlair.json') as f:
            self.flairList = json.loads(f.read())
        if modelLocation == None:
            self.createModel()
            file = self.config['Model.SavedModelLocation']
            
        self.predict_fn = tf.contrib.predictor.from_saved_model(modelLocation, signature_def_key='predict')
        self.post_vocab = tf.contrib.learn.preprocessing.VocabularyProcessor.restore(modelLocation + '/post_vocabulary.vocab')
        self.domain_vocab = tf.contrib.learn.preprocessing.VocabularyProcessor.restore(modelLocation + '/domain_vocabulary.vocab')
        self.title_vocab = tf.contrib.learn.preprocessing.VocabularyProcessor.restore(modelLocation + '/title_vocabulary.vocab')
        
    def predictAndTag(self, post):
        """
        " Performs mini transform/load of data and performs predictions with model, then tags post
        """
        try:
            posttext = post.selftext.replace('\n', ' ').replace('\r', ' ').replace('"', '\'').replace('\\', '') if post.selftext else ''
            titletext = post.title.replace('\n', ' ').replace('\r', ' ').replace('"', '\'').replace('\\', '') if post.title else ''
            domain = post.domain if not post.is_self else 'AFPSelfPost'
        except UnicodeEncodeError:
            self.logger.warning('unicode error when encoding post, skipping.')
            return
        post_transform = self.post_vocab.transform([posttext])
        title_transform = self.title_vocab.transform([titletext])
        domain_transform = self.domain_vocab.transform([domain])
        post_array = np.array(list(post_transform))
        title_array = np.array(list(title_transform))
        domain_array = np.array(list(domain_transform))
        post_array -= 1
        title_array -= 1
        domain_array -= 1
        predictions = self.predict_fn({'post': post_array, 'title': title_array, 'domain': domain_array})
        tagIndex = predictions['class_ids'][0][0]
        confidence = np.amax(predictions['probabilities'][0])*100
        self.logger.info("Prediction for: '" + post.title + "' Tag: '" + str(self.flairList[tagIndex]['flair_text']) + \
                         "' confidence: {0:.2f}%".format(confidence))
        post.flair.select(self.flairList[tagIndex]['flair_template_id'])
        self.logger.info("Post tagged.")

    def createModel(self):
        MAX_DOCUMENT_LENGTH = 0
        MAX_TITLE_LENGTH = self.config['Model.MAX_TITLE_LENGTH']
        MAX_DOMAIN_LENGTH = self.config['Model.MAX_DOMAIN_LENGTH']
        EMBEDDING_SIZE = self.config['Model.EMBEDDING_SIZE']
        MAX_LABEL = 0
        n_words_doc = 0
        n_words_title = 0
        n_words_domain = 0
        
        with open(self.config['Reddit.Subreddit']+'/RedditData.json') as f:
            data = json.loads(f.read())
            
        #Dynamically set MAX_DOCUMENT_LENGTH
        for x in data:
            if len(x["postText"].split(" ")) > MAX_DOCUMENT_LENGTH:
                MAX_DOCUMENT_LENGTH = len(x["postText"].split(" "))
                
        #We set a hard limit for processing speed and memory.
        if MAX_DOCUMENT_LENGTH > self.config['Model.MAX_DOCUMENT_LENGTH']:
            MAX_DOCUMENT_LENGTH = self.config['Model.MAX_DOCUMENT_LENGTH']
        self.config['Model.MAX_DOCUMENT_LENGTH'] = MAX_DOCUMENT_LENGTH
        self.config.write()
        
        #Dynamically set MAX_LABEL
        MAX_LABEL = len(self.flairList)

        #Take 1/10th of the data for testing after training
        self.logger.info('Reserving 1/10th of the data for testing after model is trained.')
        testData = []
        for x in range(int(len(data)/10)):
          random_index = randrange(0,len(data))
          testData.append(data.pop(random_index))

        #Load the data, process the vocabulary
        self.logger.info('Loading and performing final transformations on reddit data')
        flairArray = [x['flair_text'] for x in self.flairList]
        x_train_title = pandas.Series(x["titleText"] for x in data)
        x_train_post = pandas.Series(x["postText"] for x in data)
        x_train_domain = pandas.Series(x["domain"] for x in data)
        y_train = pandas.Series(flairArray.index(x["flairText"]) for x in data)
        
        x_test_title = pandas.Series(x["titleText"] for x in testData)
        x_test_post = pandas.Series(x["postText"] for x in testData)
        x_test_domain = pandas.Series(x["domain"] for x in testData)
        y_test = pandas.Series(flairArray.index(x["flairText"]) for x in testData)
        
        vocab_processor_doc = tf.contrib.learn.preprocessing.VocabularyProcessor(MAX_DOCUMENT_LENGTH)
        vocab_processor_domain = tf.contrib.learn.preprocessing.VocabularyProcessor(MAX_DOMAIN_LENGTH)
        vocab_processor_title = tf.contrib.learn.preprocessing.VocabularyProcessor(MAX_TITLE_LENGTH)
        
        x_transform_train_title = vocab_processor_title.fit_transform(x_train_title)
        x_transform_test_title = vocab_processor_title.transform(x_test_title)
        x_train_title = np.array(list(x_transform_train_title))
        x_test_title = np.array(list(x_transform_test_title))
        
        x_transform_train_doc = vocab_processor_doc.fit_transform(x_train_post)
        x_transform_test_doc = vocab_processor_doc.transform(x_test_post)
        x_train_post = np.array(list(x_transform_train_doc))
        x_test_post = np.array(list(x_transform_test_doc))
        
        x_transform_train_domain = vocab_processor_domain.fit_transform(x_train_domain)
        x_transform_test_domain = vocab_processor_domain.transform(x_test_domain)
        x_train_domain = np.array(list(x_transform_train_domain))
        x_test_domain = np.array(list(x_transform_test_domain))
        
        n_words_title = len(vocab_processor_title.vocabulary_)
        self.logger.info('Total unique title words: ' + str(n_words_title))
        n_words_doc = len(vocab_processor_doc.vocabulary_)
        self.logger.info('Total unique post words: ' + str(n_words_doc))
        n_words_domain = len(vocab_processor_domain.vocabulary_)
        self.logger.info('Total unique title words: ' + str(n_words_domain))
        
        #We subtract 1 from the indexes of all words.  This is because the VocabProcessor uses 0
        # for 'no data', but the model uses -1 for 'no data'
        x_train_title -= 1
        x_train_post -= 1
        x_train_domain -= 1
        x_test_title -= 1
        x_test_post -= 1
        x_test_domain -= 1
        
        #Config for tf estimator
        config = tf.contrib.learn.RunConfig(gpu_memory_fraction=0.9)
        
        #Setup the classifier and features before learning
        bow_column_title = tf.feature_column.categorical_column_with_identity('title', num_buckets=n_words_title)
        bow_embedding_column_title = tf.feature_column.embedding_column(bow_column_title, dimension=EMBEDDING_SIZE)
        bow_column_post = tf.feature_column.categorical_column_with_identity('post', num_buckets=n_words_doc)
        bow_embedding_column_post = tf.feature_column.embedding_column(bow_column_post, dimension=EMBEDDING_SIZE)
        bow_column_domain = tf.feature_column.categorical_column_with_identity('domain', num_buckets=n_words_domain)
        bow_embedding_column_domain = tf.feature_column.embedding_column(bow_column_domain, dimension=EMBEDDING_SIZE)
        classifier = tf.estimator.DNNLinearCombinedClassifier(
            n_classes=MAX_LABEL,
            linear_feature_columns=[bow_column_title, bow_column_post, bow_column_domain],
            dnn_feature_columns=[bow_embedding_column_post, bow_embedding_column_title, bow_embedding_column_domain],
            dnn_hidden_units=[self.config['Model.DNN.Layer1'], self.config['Model.DNN.Layer2']],
            dnn_dropout=self.config['Model.DNN.DROPOUT_RATE'],
            config=config)
        
        # Train.
        self.logger.info('Training the model.')
        self.logger.info('This will take a number of minutes depending on your settings and hardware.')
        train_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={'post': x_train_post, 'title': x_train_title, 'domain': x_train_domain},
            y=y_train,
            batch_size=self.config['Model.BATCH_SIZE'],
            num_epochs=self.config['Model.NUM_EPOCHS'],
            shuffle=True)
        #May want to add hooks into this in the future for watching progress
        classifier.train(input_fn=train_input_fn)
        self.logger.info('Model has been trained, performing predictions on test data.')
        
        # Predict.
        test_input_fn = tf.estimator.inputs.numpy_input_fn(
            x={'post': x_test_post, 'title': x_test_title, 'domain': x_test_domain},
            y=y_test,
            num_epochs=1,
            shuffle=False)
        predictions = classifier.predict(input_fn=test_input_fn)
        
        # Score with tensorflow.
        scores = classifier.evaluate(input_fn=test_input_fn)
        self.logger.info('Final Accuracy: {0:.2f}%'.format(scores['accuracy']*100))
        
        garbage = input('Is this accuracy good enough for you?  If not, quit now.  Else, hit enter to continue')
        
        self.logger.info('Saving model and vocabularies...')
        #Function used for input of predictions are model is loaded from file
        def serving_input_receiver_fn():
            inputs = {"post": tf.placeholder(shape=[1,MAX_DOCUMENT_LENGTH], dtype=tf.int64),
                      "title": tf.placeholder(shape=[1,MAX_TITLE_LENGTH], dtype=tf.int64),
                      "domain": tf.placeholder(shape=[1,MAX_DOMAIN_LENGTH], dtype=tf.int64)}
            return tf.estimator.export.ServingInputReceiver(inputs, inputs)
        
        SAVED_LOCATION = classifier.export_savedmodel(self.config['Reddit.Subreddit'], serving_input_receiver_fn)
        SAVED_LOCATION = SAVED_LOCATION.decode()
        vocab_processor_doc.save(SAVED_LOCATION+'/post_vocabulary.vocab')
        vocab_processor_domain.save(SAVED_LOCATION+'/domain_vocabulary.vocab')
        vocab_processor_title.save(SAVED_LOCATION+'/title_vocabulary.vocab')
        
        self.config['Model.SavedModelLocation'] = SAVED_LOCATION
        self.config.write()
        self.logger.info('Model saved. Proceeding.')

