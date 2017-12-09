###
# Main file for AutoFlairPost
###
import configobj
import logging
import os
import app.redditAccount


if __name__ == '__main__':
    #cd to script directory
    os.chdir(os.path.dirname(__file__))
    
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
    logger.info('Logger Initiated')
    
    #Get/setup reddit account
    redditAccount = app.redditAccount.RedditAccount(config, logger)
    
    #if needed, perform ETL of reddit data
    if os.path.isdir(config['Reddit.Subreddit']):
        #check for saved model and run tagger
        pass
    else:
        os.mkdir(config['Reddit.Subreddit'])
        logger.info('No saved models detected, running ETL (extract, transform, load) of Reddit data')
        redditAccount.extractData()