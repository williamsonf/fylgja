'''
fylgja/utils/messages.py - Bundles incoming/outgoing open ai messages with relevant metadata
Copyright (c) 2023 Frederick T Williamson

Classes:
    Message: Bundles incoming/outgoing open ai messages with relevant metadata

@author: Fred Williamson
'''
import logging, tiktoken, os
import pandas as pd

logging.info('fylgja.utils.messages.py - Loading utils.messages.py')

class Message(object):
    '''
    A class used to bundle messages with relevant metadata.
    
    This class essentially serves as a way to bundle an array of message objects
    utilized by the Open AI API's chat completion alongside relevant metadata
    for Fylgja's purposes.

    Attributes:
        source (str): The originating source of the message (ie. discord)
        user (int): a numeric id used to identify the user, often source-specific
        chat (list): an array of message objects. for further information, see Open AI's Chat Completion guide
        verified (bool): whether the message comes from a verified user or not. usually, if this is false then the message is awaiting verification; unverified messages should be tossed
        state (bool): whether the message is an outgoing prompt awaiting a response from Fylgja, or if it is an outgoing response waiting to be displayed to the user. True = response, False = prompt
        df (pd.DataFrame): a dataframe containing the user's chat log
        user_info (dict): a possible extra piece of context used to identify the user to the bot
        context (list): a list which will be used to construct the conversation's context
        tokens (int): maximum allowed tokens for this user
        tries (int): the number of times the message has been sent to open ai api and failed
        
    Methods:
        flag_verified(): Flips the verified attribute to True
        flag_response(chat): Updates the carried Message with the output message, and additionally flips the state attribute to True
        construct_context(): Builds the chat context, complete with necessary system prompts and the user's input
        count_tokens():
    '''

    def __init__(self, source: str, user: int, chat: list) -> None:
        '''
        Constructor
        '''
        logging.debug('fylgja.utils.messages.py - Instantiating a new Message class')
        self.source = source
        self.user = user
        self.chat = chat
        self.verified = 0 #boolean, either verified or not
        self.state = 0 #0 for prompt, 1 for response
        self.df = None #the pandas dataframe holding the chatlog
        self.user_info = None
        self.context = []
        self.tokens = 0
        self.tries = 0
        
    def flag_verified(self) -> "Message":
        self.verified = 1
        logging.info("fylgja.utils.messages.py - Message flagged verified. (Src: {}, User: {})".format (self.source, str(self.user)))
        return self
        
    def flag_response(self) -> "Message":
        self.state = 1
        logging.info("fylgja.utils.messages.py - Message flagged response. (Src: {}, User: {})".format(self.source, str(self.user)))
        return self
    
    def construct_context(self) -> None:
        #sorting in descending order; most recent messages first
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.sort_values(by='timestamp', ascending=False)
        
        #we no longer need to add our latest message to the context because it will be part of the dataframe, i think?
        #self.context.append({'role' : 'user', 'content' : str(self.chat)})
        
        #getting our usable token amount
        self.tokens -= 3
        for message in self.context:
            self.tokens -= self.count_tokens(message['content'])
            
        #now, we fill context with remaining messages
        for index, row in self.df.iterrows():
            new_msg = {'role' : row[1], 'content' : row[2]}
            self.context.append(new_msg)
            self.tokens -= self.count_tokens(row[2])
            if self.tokens <= 0:
                break
        
        self.context.append(self.user_info)    
        self.context.append({'role' : 'system', 'content' : os.environ.get('SYSTEM_PROMPT')})
        self.context.reverse() #reverse it so that it's in the correct order
        
    def count_tokens(self, msg: str) -> int:
        '''
        This method count_tokens takes in a string msg as an argument and returns
        the number of tokens present in the string. The token count is calculated
        by encoding the string using the GPT-3.5-turbo encoding model and returning
        the length of the encoded string.
        
        Args:
            msg (str): A string to count the tokens for
        Returns:
            int: The number of tokens present in the given string
        '''
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(msg))+4