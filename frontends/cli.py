'''
fylgja/frontends/cli.py
Copyright (c) 2023 Frederick T Williamson
'''
import logging
from utils.messages import Message

logging.info('fylgja.frontends.cli.py - Loading frontends.cli.py')

class CommandLineInterface(object):
    '''
    classdocs
    '''


    def __init__(self, queue: "Queue"):
        '''
        Constructor
        '''
        self.queue = queue
        
    def receive_msg(self, prompt: str) -> None:
        msg = Message("cmd", 1, str(prompt))
        self.queue.put(msg)
        
    def post_msg(self, response: Message) -> None:
        print(str(response.chat['content']))
        
    def start(self, is_running: bool) -> None:
        logging.info("fylgja.frontends.cli.py - Starting a CommandLineInterface listener!")
        while is_running:
            u_in = input("")
            self.receive_msg(u_in)
        logging.info("fylgja.frontends.cli.py - CommandLineInterface listener is ending!")