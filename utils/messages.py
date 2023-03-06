'''
fylgja/utils/messages.py - Bundles incoming/outgoing open ai messages with relevant metadata
Copyright (c) 2023 Frederick T Williamson

Classes:
    Message: Bundles incoming/outgoing open ai messages with relevant metadata

@author: Fred Williamson
'''
import logging

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
        path (str): A path containing the relevant chat logs
        
    Methods:
        flag_verified(): Flips the verified attribute to True
        flag_response(chat): Updates the carried Message with the output message, and additionally flips the state attribute to True
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
        self.path = None
        
    def flag_verified(self) -> "Message":
        self.verified = 1
        logging.info("fylgja.utils.messages.py - Message flagged verified. (Src: {}, User: {})".format (self.source, str(self.user)))
        return self
        
    def flag_response(self) -> "Message":
        self.state = 1
        logging.info("fylgja.utils.messages.py - Message flagged response. (Src: {}, User: {})".format(self.source, str(self.user)))
        return self