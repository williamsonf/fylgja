'''
fylgja/frontends/frontends.py
Copyright (c) 2023 Frederick T Williamson

All frontend objects should inherit from the dummy class Frontend.
In order to then function as a Frontend for the Fylgja pipeline, the following

'''

import logging, queue, os, inspect

logging.info(f'Loading frontends.frontends.py')

class Frontend():
    '''
    '''
    def __init__(self, q=queue.Queue):
        logging.info(f'Instantiating a new {self.__class__.__name__} object, SOURCE: {os.path.abspath((inspect.stack()[1])[1])}')
        self.q = q
        
    def start(self) -> bool:
        '''
        A dummy method. Overload this with all necessary code to connect to the frontend.
        Return True if a connection was succesfully made, else False.
        '''
        return True
    
    def receive_msg(self) -> bool:
        '''
        A dummy method. Overload this with input processing. This method should put a 
        Message object into the queue.
        Return True if the message was successfully processed, else False.
        '''
        return True
    
    def post_msg(self) -> bool:
        '''
        A dummy method. Overload this with the logic for serving the contents of a Message
        object to the correct recipient, utilizing the Message.user and Message.user and Message.source attributes.
        Return True if a message was successfully posted, else False.
        '''
        return True