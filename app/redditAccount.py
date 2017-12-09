import praw
import json

class RedditAccount(object):
    def __init__(self, config, logger, *args, **kwargs):
        self.config = config
        self.logger = logger
        self.logger.info("Initiating RedditAccount")
        
        if self.config['Reddit.Subreddit'] == '':
            self.firstTimeSetup()
            
        self.logger.info("Creating Reddit connection")
        reddit = praw.Reddit(client_id=self.config['Reddit.AppID'],
                 client_secret=self.config['Reddit.AppSecret'],
                 user_agent='AutoFlairPost by ArtificialQualia',
                 username=self.config['Reddit.AccountName'],
                 password=self.config['Reddit.Password'])
        self.subreddit = reddit.subreddit(self.config['Reddit.Subreddit'])
        self.logger.info("Reddit connection created")
            
    def firstTimeSetup(self):
        self.logger.info("RedditAccount config is empty.  Running first time setup.")
        self.config['Reddit.Subreddit'] = input("Please enter the subreddit this app will be used for: ")
        self.config['Reddit.AccountName'] = input("Please enter the Reddit account name that will be tagging posts (NOTE: must have flair mod permissions): ")
        self.config['Reddit.Password'] = input("Please enter the account password: ")
        print("If you have not already set up the 'app' connection on Reddit, please do so now. See README.md for instructions.")
        self.config['Reddit.AppID'] = input("Please enter the Reddit app ID: ")
        self.config['Reddit.AppSecret'] = input("Please enter the Reddit app secret: ")
        self.config.write()
        self.logger.info("RedditAccount first time setup complete.")
        
    def getFlairList(self):
        flairList = []
        for flair in self.subreddit.new().next().flair.choices():
            flairList.append(flair['flair_text'])
        return flairList
    
    def extractData(self):
        if self.config['Reddit.data.NumberOfPostsToExtract'] == '':
            print("\nWe need to know how many posts to grab from the history of your subreddit, starting from the most recent.")
            print("You want it to be as high as possible while containing good data.")
            print("This means posts that contain proper tags, and that you haven't changed your tags/tagging standards for all the posts this number will contain.")
            print("Choose this number carefully. It should be at least 1000, 5000 is good, 10k+ is excellent, but choose quality over quantity.")
            self.config['Reddit.data.NumberOfPostsToExtract'] = int(input("Enter the number of posts to retrieve: "))
            self.config.write()
        
        self.logger.info("Getting the posts from Reddit, depending on how many posts you specified this may take a few minutes...")
        flairList = self.getFlairList()
        submissionIterator = self.subreddit.submissions()
        outputData = []
        for post in submissionIterator:
            if post.link_flair_text not in flairList:
                self.logger.warning('No or non-standard flair on post, ignoring post ' + post.id)
                continue
            try:
                posttext = post.selftext.replace('\n', ' ').replace('\r', ' ').replace('"', '\'').replace('\\', '') if post.selftext else ''
                titletext = post.title.replace('\n', ' ').replace('\r', ' ').replace('"', '\'').replace('\\', '') if post.title else ''
                domain = post.domain if not post.is_self else 'AFPSelfPost'
                outputData.append({"flairText": str(post.link_flair_text), "titleText": str(titletext), "postText": str(posttext), "domain": str(domain) })
            except UnicodeEncodeError:
                self.logger.warning('unicode error, ignoring post ' + post.id)
                continue
            if len(outputData) >= self.config['Reddit.data.NumberOfPostsToExtract']:
                break
        self.logger.info("Finished getting Reddit posts.  Saving data to ./"+self.config['Reddit.Subreddit']+'/RedditData.json')
        with open(self.config['Reddit.Subreddit']+'/RedditData.json', 'w') as f: 
            bytesWritten = json.dump(outputData, f)