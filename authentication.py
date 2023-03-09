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

Classes:
    CsvAuth: A simple class for handling all major authentication functions, using a csv file to store information. 
        Intended for proof of concept use.

@author: Fred Williamson
'''
import csv, logging, dotenv, os, datetime, pathlib
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
        whitelist (str): The filepath for the whitelist csv, obtained from .env
    
    Methods:
        validate(): checks the whitelist csv for matching frontend:frontend ID pairs, returns the user's information if valid
        construct_log(): Constructs a chat log file for a given user if it doesn't exist or opens an existing one and returns a Pandas DataFrame
        return_to_queue(): returns the message to the queue
        log_message(message): adds a new message to the chat log
        get_logpath(message): gets the path for chat logs
    '''

    def __init__(self, queue: 'Queue') -> None:
        '''
        '''
        logging.debug('fylgja.authentication.py - Instantiating a new CsvAuth class')
        self.queue = queue
        self.whitelist = os.environ.get('CSV_WHITELIST')
        
    def validate(self, message: "Message") -> bool:        
        '''
        Check if the source and user of the message are present in the whitelist file.

        Reads a whitelist CSV file specified by self.whitelist and searches for a matching row where
        the value in the `self.message.source` column equals self.message.user.

        If a matching row is found, the flag_verified method of the self.message object is called and
        the function returns True. If no matching row is found, the function returns False.

        Returns:
            bool: True if a matching row was found in the whitelist file, False otherwise.
        '''
        with open(self.whitelist, 'r', encoding="utf-8") as csvfile:
            whitelist = csv.DictReader(csvfile)
            for row in list(whitelist):
                if str(row[message.source]) == str(message.user): #did our user match one of the ones in the source column?
                    if len(row['system'])  > 0: #if the user has a system identifier set for the bot to see
                        message.user_info = {'role' : 'system', 'content' : row['system']}
                    message.tokens = int(row['limit'])
                    message.flag_verified()
                    return True
            else:
                logging.info('fylgja.authentication.py - Message Authentication failed! Type: CSV, Source: {}, User ID: {}'.format(str(self.message.source), str(self.message.user)))
                return False
    
    def construct_log(self, message: "Message") -> pd.DataFrame:
        '''
        Constructs a chat log file for a given user if it doesn't exist or opens an existing one and returns a Pandas DataFrame.
        
        Args:
            message: A Message object representing the message to be logged.
            
        Returns:
            DataFrame
            
        Raises:
            IOError: If the log file cannot be created or opened.
            
        This method reads a whitelist CSV file to obtain the username for the given message. Then it constructs a path
        to the chat log file for the user by concatenating the value of the 'CHATLOGS' environment variable, the username,
        and the '.csv' extension. The chat log file is opened and loaded into a Pandas DataFrame. If the file does not
        exist, it is created and an empty DataFrame is returned.
        '''
        path = self.get_logpath(message)        
        logging.debug("fylgja.authentication.py - Constructing chatlogs from path {}".format(path))
        
        df = None
        if path.is_file():
            #loading our chat logs into a dataframe
            df = pd.read_csv(path, names=['timestamp', 'role', 'content'])
            #sorting in descending order; most recent messages first
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values(by='timestamp', ascending=False)
                            
        elif not path.is_file():
            logging.info('fylgja.authentication.py - No file {} exists. Creating one now.'.format(str(path)))
            #we create an empty file
            with open(path, 'w', encoding="utf-8") as _:
                pass
            df = pd.DataFrame(columns=['timestamp', 'role', 'content'])
            
        message.df = df    
        return df
                                        
    def return_to_queue(self, message: "Message") -> None:
        '''
        Returns the message to the queue.

        This method puts the message back into the queue so that it can be processed again by another worker.
        '''
        logging.info("fylgja.authentication.py - Returning a message to the queue")
        self.queue.put(message)
        
    def log_message(self, message: "Message") -> None:
        '''
        Logs the given message to the specified CSV file.
        
        Args:
            message (dict): A message object, containing the message to be logged in its chat field
        '''
        path = self.get_logpath(message)
        role = None
        content = None
        if message.verified:
            if not message.state:
                role = 'user'
                content = message.chat
            elif message.state:
                role = 'assistant'
                content = message.chat['content']
            else:
                logging.critical('fylgja.authentication.py - A verified message is neither a prompt or a response! User: {}, Src: {}, Msg: {}'.format(str(message.user), str(message.source), str(message.chat)))
            
        if role and content: #if both fields have been filled, we can save the chat field
            new_row = {'timestamp' : datetime.datetime.now(), 'role' : role, 'content' : content}
            new_row = pd.DataFrame(new_row, index=[0])
            message.df = pd.concat([message.df, new_row])
            message.df.to_csv(path, index=False, header=False)
        
    def get_logpath(self, message: "Message") -> str:
        with open(self.whitelist, 'r', encoding="utf-8") as csvfile:
            whitelist = csv.DictReader(csvfile)
            for row in list(whitelist):
                if str(row[message.source]) == str(message.user):
                    username = row['username']
        path = pathlib.Path(os.environ.get('CHATLOGS') + username + ".csv")
        return path