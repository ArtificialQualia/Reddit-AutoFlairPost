# What is it?
Reddit-AutoFlairPost is a utility for Reddit moderators who want a little help tagging new posts.  
It inspects your existing submissions and flair in order to build a Machine Learning model to automatically tag new posts.  
Most subreddits with good tagging standards and distinct categories can get over 60% accuracy using this tool.  Some go as high as 90%+.  
Even if you get a lower accuracy with this tool, it can still be very helpful to initially tag a post while other mods are not available.  
The tool uses the post content, the title, and the domain of the post in order to predict what it should be tagged as.

# How to use it
To use AutoFlairPost, you'll have to do some setup ahead of time.
## Reddit setup
Sorry this is a bit of a pain to setup.  Hopefully this will be easier in the future.  
1. Create a Reddit account that AutoFlairPost will use to tag posts.  Make sure you add the account to your moderator list, and that it has flair permissions.  
2. While logged in with your new account, go to: https://www.reddit.com/prefs/apps/
3. Hit the 'are you a developer? create an app...' button.
    1. Input whatever name you want
    2. Choose 'script'
    3. Input whatever description you want
    4. You can skip 'about url'
    5. Input http://localhost:80 for 'redirect uri'
    6. Hit 'create app'
4. Your application should be created.  Make note of the app ID (numbers and letters directly below 'personal use script') and 'secret'.  You will need these values later.  
## Server setup
Perform these steps on the server/desktop you plan to run AutoFlairPost on.  
1. Install Python 3.5
2. Download the latest release of AutoFlairPost as a zip file.  You can get that here: https://github.com/ArtificialQualia/Reddit-AutoFlairPost/releases
3. Unzip to wherever you want.
4. Open a terminal and cd to where you unzipped AutoFlairPost
5. Run 'pip install -r requirements.txt'
6. Run 'python AutoFlairPost.py' and AutoFlairPost will walk you through initialization and building your model.  After the model is built, AutoFlairPost will automatically start tagging your posts.
After you have built and saved your model, you can simply run 'python AutoFlairPost.py' anytime to start tagging posts without having to build another model.

# Advanced configuration
If you want to mess with some of the Machine Learning settings that are used to build the model, edit AutoFlairPost.config before building your model.

# Problems?
If you encounter any problems with AutoFlairPost, please submit an issue here: https://github.com/ArtificialQualia/Reddit-AutoFlairPost/issues