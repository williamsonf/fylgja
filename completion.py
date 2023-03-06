'''
fylgja/completion.py
Copyright (c) 2023 Frederick T Williamson

@author: Fred Williamson
'''
import openai, datetime, os, dotenv, logging, csv

dotenv.load_dotenv()

logging.info('fylgja.completion.py - Loading completion.py')
openai.organization = os.environ.get('OPENAI_ORG')
openai.api_key = os.environ.get('OPENAI_API_KEY')

class ChatCompletion(object):
    '''
    This class is a no frills back and forth with the Open AI API.
    It takes an array of messages from a Message object (see utils.messages),
    it sends those messages to Open AI's chat completion model.
    Once the response is received:
        -It saves the response to the user's chat log
        -It overwrites the Message object's chat attribute with the new response & flags the Message as a response
        -It returns the Message object to the Queue, to be sent back out
        
    Attributes:
        queue (Queue): a Queue object (see python's standard model, queue), which the message should be deposited in
        message (Message): a Message object (see utils.message) containing the prompt/chat log and associated metadata
        
    Methods:
        get_response(): calls the open ai api, returns just the part we care about
        log_response(): appends the originating user's chat log with the response
        return_to_queue(): returns the message to the queue
    '''

    def __init__(self, queue: 'Queue', message: 'Message') -> None:
        '''
        Constructor
        '''
        logging.debug('fylgja.completion.py - Instantiating a new ChatCompletion class')
        if message.verified:
            self.queue = queue
            self.message = message
            self.model = os.environ.get('MODEL')
            self.response = self.get_response()
            self.log_response()
            self.message.chat = self.response
            self.message.flag_response()
            self.return_to_queue()
        else:
            logging.critical("fylgja.completion.py - An unverified message has breached containment! (Src: {}, User: {})".format (self.message.source, str(self.message.user)))
        
    def get_response(self) -> dict:
        logging.info("fylgja.completion.py - Calling Open AI for a chat completion.")
        response = openai.ChatCompletion.create(
            model= self.model,
            messages= self.message.chat)
        logging.debug("Response received: {}".format(str(response)))
        
        return response['choices'][0]['message']
    
    def log_response(self) -> None:
        logged = [datetime.datetime.now(), self.response["role"], self.response["content"]]
        with open(self.message.path, 'a', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(logged)
            
    def return_to_queue(self) -> None:
        '''
        Returns the message to the queue.

        This method puts the message back into the queue so that it can be processed again by another worker.
        '''
        logging.info("fylgja.completion.py - Returning a message to the queue")
        self.queue.put(self.message)