'''
fylgja/frontends/cli.py
Copyright (c) 2023 Frederick T Williamson
'''
import logging, os, sys
from utils.messages import Message
from .frontends import Frontend

logging.info(f'Loading frontends.cli.py')

class CommandLineInterface(Frontend):
    '''
    classdocs
    '''


    def __init__(self, q: "Queue"):
        '''
        Constructor
        '''
        super().__init__(q)
        
    def receive_msg(self, prompt: str) -> bool:
        try:
            msg = Message("cmd", 1, str(prompt))
            self.q.put(msg)
        except:
            return False
        
    def post_msg(self, response: Message) -> None:
        try:
            print(str(response.chat['content']))
        except:
            return False
        
    def start(self, is_running: bool) -> None:
        logging.info(f"Starting a CommandLineInterface listener!")
        try:
            while is_running:
                u_in = input("")
                self.receive_msg(u_in)
        except KeyboardInterrupt:
            sys.exit()
        except:
            return False
        logging.info(f"CommandLineInterface listener is ending!")