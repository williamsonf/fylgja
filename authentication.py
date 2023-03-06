'''
fylgja/authentication.py - Authenticates user messages and prepares them for chat completion.
Copyright (c) 2023 Frederick T Williamson

Authentication classes are used to do exactly that. When supplied with a Message
class object (see utils.messages), they will check the user id within that Message's
metadata against a white list.

Accepted users can have one user id stored per supported front end. Each user id-front end
pair must be unique. That is, if communication through the popular chat app Scrimblojournal
were supported, then a given Scrimblojournal account should only be listed in the whitelist
once.

Once verified, the user's maximum token limit should be checked against:
    -The token length of their stored System message (generally used to identify them to the bot)
    -The token length of any preceding chat messages between user and bot which have been stored
    -The token length of their current prompt
A new message object array should be constructed beginning with key System messages, followed by
the most recent stored chat messages and ending in the user's prompt. This new message array should
not be of a greater token size than the user's token limit.

This new message array replaces the Message object's old message attribute, and the
Message object's verified status is set to True.

Classes:
    CsvAuth: A simple class for handling all major authentication functions, using a csv file to store information. 
        Intended for proof of concept use.

@author: Fred Williamson
'''
import csv, logging, tiktoken, dotenv, os, datetime
import pandas as pd

dotenv.load_dotenv()

logging.info('fylgja.authentication.py - Loading authentication.py')

class CsvAuth(object):
    '''
    A simple class for authenticating and updating messages, using a csv file for the white list.
    
    The whitelist csv file should be formatted as follows:
    Username, Token Limit, System, Frontend1 ID, Frontend2 ID, ...
    
    For a better explanation of how the whitelist csv is read, please refer to
    the csv module's documentation regarding the csv.DictReader() function
    
    The chat log file should use the naming convention username.csv where username is the Username from the whitelist csv
    The file path to the whitelist csv should be stored in .env under the variable CSV_WHITELIST
    The file path to the folder containing username.csv should be stored in .env under the variable CHATLOGS
    
    Attributes:
        queue (Queue): a Queue object (see python's standard model, queue), which the message should be deposited in once authorization is finished
        message (Message): a Message object (see utils.message) containing the prompt/chat log and associated metadata
        whitelist (str): The filepath for the whitelist csv, obtained from .env
        user (dict): Returns False if authentication has failed. Otherwise, a dictionary containing the User and their associated System message
        free_tokens (int): The number of tokens available for use in constructing the chat context, taking into consideration the user's token limit, 
            the length of their system prompt and the length of the current prompt
        msg_construct (list): An array of message objects, used to hold the different pieces of the chat's context until they are fully assembled.
    
    Methods:
        validate(): checks the whitelist csv for matching frontend:frontend ID pairs, returns the user's information if valid
        count_tokens(msg): Takes a message and returns the number of Open AI tokens it would use.
        construct_log(): reads the user's chatlog, then takes the most recent to provide context in chat completion
        return_to_queue(): returns the message to the queue
        log_message(path, df, msg): adds a new message to the chat log
    '''

    def __init__(self, queue: 'Queue', message: 'Message') -> None:
        '''
        The __init__ method initializes an instance of the CsvAuth class, which is responsible for handling authentication via CSV files.

        Parameters:

        queue: A Queue object representing the message queue.
        message: A Message object representing the message to be authenticated.
        
        Returns:
        None
        
        This method validates the user in the CSV whitelist and constructs a message accordingly. 
        If authentication is successful, it updates the free_tokens attribute and constructs a log message before returning the message to the queue. 
        If authentication fails, it logs a message indicating the failure.
        '''
        logging.debug('fylgja.authentication.py - Instantiating a new CsvAuth class')
        self.queue = queue
        self.message = message
        self.whitelist = os.environ.get('CSV_WHITELIST')
        self.free_tokens = 0
        self.msg_construct = [{"role" : "system", "content" : os.environ.get('SYSTEM_PROMPT')}]
        
        self.user = self.validate()
        if self.user:
            self.message.flag_verified()
            self.free_tokens = int(self.user['limit']) - ( self.count_tokens(self.user['system']) + self.count_tokens(self.message.chat) ) #setting our free tokens
            self.msg_construct.append({"role" : "system", "content" : self.user["system"]})
            self.construct_log()
            self.return_to_queue()
        else:
            logging.warning('fylgja.authentication.py - Message Authentication failed! Type: CSV, Source: {}, User ID: {}'.format(str(self.message.source), str(self.message.user)))
        
    def validate(self) -> bool:        
        '''
        Check if the source and user of the message are present in the whitelist file.

        Reads a whitelist CSV file specified by self.whitelist and searches for a matching row where
        the value in the `self.message.source` column equals self.message.user.

        If a matching row is found, the flag_verified method of the self.message object is called and
        the function returns a dictionary with relevant information. If no matching row is found, the function returns False.

        Returns:
            bool: True if a matching row was found in the whitelist file, False otherwise.
        '''
        with open(self.whitelist, 'r', encoding="utf-8") as csvfile:
            whitelist = csv.DictReader(csvfile)
            for row in list(whitelist):
                if str(row[self.message.source]) == str(self.message.user):
                    result = {'username' : row['username'], 'limit' : row['limit'] , 'system' : row['system']}
                    return result
            else:
                return False
            
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
        return len(encoding.encode(msg))
    
    def construct_log(self) -> None:
        '''
        Reads the chat logs for the authenticated user and constructs a chat history 
        based on the messages saved in the logs. The chat history is stored in the 
        msg_construct attribute of the CsvAuth instance, along with the free tokens 
        remaining for the user. The chat history is constructed by iterating over the 
        rows of the chat log file, sorted in ascending order by timestamp, until the 
        available free tokens are exhausted or all messages are included.
        
        Also necessary for setting the message's path attribute
        '''
        path = os.environ.get('CHATLOGS') + self.user['username'] + ".csv"
        self.message.path = path
        prompt = {"role" : "user", "content" : self.message.chat}
        
        logging.debug("fylgja.authentication.py - Constructing chatlogs from path {}".format(path))

        try:
            #loading our chat logs into a dataframe
            df = pd.read_csv(path, names=['timestamp', 'role', 'content'])
            #sorting in descending order; most recent messages first
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp', ascending=False)
            
            builder = []
        
            #we now iterate over the dataframe
            for index, row in df.iterrows():
                msg = {'role' : row[1], 'content' : row[2]}
                builder.append(msg)
                self.free_tokens -= self.count_tokens(row['content'])
                #if we've run out of tokens, there's no need to continue
                if self.free_tokens <= 0:
                    break
            builder.reverse()
            self.msg_construct.extend(builder)
                
            self.log_message(path, df, prompt)
                
        except:
            logging.info('fylgja.authentication.py - No file {} exists. Creating one now.'.format(str(path)))
            with open(path, 'w', encoding="utf-8") as new:
                writer = csv.writer(new)
                new = {"timestamp" : datetime.datetime.now(), "role" : prompt['role'], "content" : prompt['content']}
                writer.writerow(new.values())
                            
        self.msg_construct.append(prompt)
        self.message.chat = self.msg_construct
            
    def return_to_queue(self) -> None:
        '''
        Returns the message to the queue.

        This method puts the message back into the queue so that it can be processed again by another worker.
        '''
        logging.info("fylgja.authentication.py - Returning a message to the queue")
        self.queue.put(self.message)
        
    def log_message(self, path: str, df: pd.DataFrame, msg: dict) -> None:
        '''
        Logs the given message to the specified CSV file.
        
        Args:
            path (str): The path to the CSV file.
            df (pd.DataFrame): The DataFrame representing the CSV file.
            msg (dict): A dictionary representing the message to log. Must have 'role' and 'content' keys.
        '''
        new_row = {'timestamp' : datetime.datetime.now(), 'role' : msg["role"], 'content' : msg['content']}
        new_row = pd.DataFrame(new_row, index=[0])
        df = pd.concat([df, new_row])
        df.to_csv(path, index=False, header=False)