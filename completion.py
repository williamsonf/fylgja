'''
fylgja/completion.py
Copyright (c) 2023 Frederick T Williamson

@author: Fred Williamson
'''
import openai, datetime, os, dotenv, logging, csv

dotenv.load_dotenv()

logging.info(f'Loading completion.py')
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
        model (str): The model that this ChatCompletion instance should utilize
        
    Methods:
        get_response(): calls the open ai api, returns just the part we care about
        return_to_queue(): returns the message to the queue
    '''

    def __init__(self, queue: 'Queue', model: str) -> None:
        '''
        Constructor
        '''
        logging.debug(f'Instantiating a new ChatCompletion class')
        self.queue = queue
        self.model = model
        
    def get_response(self, message: "Message") -> None:
        logging.info(f"Calling Open AI for a chat completion.")
        if message.tries < 3:
            try:
                response = openai.ChatCompletion.create(
                    model= self.model,
                    messages= message.context)
                logging.debug("Response received: {}".format(str(response)))
            
                message.chat = response['choices'][0]['message']
                message.flag_response()
            except:
                message.context = []
                message.tries += 1
        else:
            message.chat = '[Critical Error: Could not reach OpenAI API.]'
            message.flag_response()
                
    def return_to_queue(self, message: "Message") -> None:
        '''
        Returns the message to the queue.

        This method puts the message back into the queue so that it can be processed again by another worker.
        '''
        logging.info(f"Returning a message to the queue")
        self.queue.put(message)