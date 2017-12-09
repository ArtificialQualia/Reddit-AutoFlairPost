###
# Main file for AutoFlairPost
###
import configobj
import logging
import os
import app.redditAccount
import app.model


if __name__ == '__main__':
    #cd to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    #load config
    config = configobj.ConfigObj('AutoFlairPost.config', unrepr=True)
    
    #Grab logging level from config
    numeric_level = getattr(logging, config['LogLevel'].upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid LogLevel: %s \nPlease fix AutoFlairPost.config' % config['LogLevel'])
    
    ###
    #setup logging
    ###
    logger = logging.getLogger(__name__)
    logger.setLevel(numeric_level)
    #create log file handler
    file_handler = logging.FileHandler('AutoFlairPost.log')
    file_handler.setLevel(numeric_level)
    #create console stream handler
    console_stream = logging.StreamHandler()
    console_stream.setLevel(numeric_level)
    #enforce same format on both handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    console_stream.setFormatter(formatter)
    #add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_stream)
    logger.info('Libraries loaded, logger initiated')
    
    #Get/setup reddit account
    redditAccount = app.redditAccount.RedditAccount(config, logger)
    
    #create subdirectory for subreddit specific data and models
    if not os.path.isdir(config['Reddit.Subreddit']):
        os.mkdir(config['Reddit.Subreddit'])
        
    #if needed, perform ETL of reddit data
    if not os.path.isfile(config['Reddit.Subreddit']+"/RedditData.json") or not os.path.isfile(config['Reddit.Subreddit']+"/RedditFlair.json"):
        logger.info('No saved reddit data detected, running extract and transform of Reddit data')
        redditAccount.extractData()
    
    #if needed, train a new model
    if config['Model.SavedModelLocation'] == '':
        logger.info('No saved model detected, creating a new one...')
        model = app.model.Model(config, logger)
    else:
        logger.info('Loading saved model...')
        model = app.model.Model(config, logger, modelLocation=config['Model.SavedModelLocation'])
        logger.info('Model loaded')
        
    #Start tagging posts!
    redditAccount.monitorSubmissions(model)