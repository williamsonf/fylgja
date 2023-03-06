'''
fylgja/main.py
Copyright (c) 2023 Frederick T Williamson

The main file for Fylgja, which will take input from whatever front ends
we may use (ie. discord, cmd, etc.) and store them in a queue. It will then
receive responses and dole those out to the front end accordingly through
the same queue.

The Queue will consist of Prompts, Authenticated Prompts, and Responses.
The lifespan of a Prompt -> Response looks like so:

First, the Front End (Discord, Cmd, etc.) receives a Prompt from a user.
The prompt is sent to the Queue alongside certain identifying metadata. Example
metadata includes the originating frontend (ie. "This is from Discord!"), and an
identification for the user (The discord user id of the sender).

Prompts are removed from the Queue in a First Come, First Serve fashion. They are
initially sent to our Authentication model, where the identifying metadata is used
to validate the user. If the user is valid, the prompt itself is potentially
altered by prepending data specific to that user. The prompt is then flagged
as an Authenticated Prompt and returned to the queue.
If the prompt fails Authenticated, it is discarded.
All prompts and their users should be logged at this stage.

Authenticated Prompts are passed to our chosen AI Transformer. At the time of
writing, the chosen transformer for this task is Open AI's gpt-3.5-turbo
Once the transformer has supplied a response, the identifying metadata is reattached
and the Response is placed back in the queue.

Responses are returned to their associated Front End as identified via their 
metadata.
The metadata is then further employed to display the prompt to the correct 
user.
Responses are logged.

Prompts/responses should be accompanied by the following metadata fields:
source
    The source of the data (ie. Discord)
user
    A user identifier (ie. Discord User ID)
state
    boolean. 0 == Prompt, 1 == Response
verified
    boolean. 0 == Awaiting authentication. 1 == authenticated
    Prompts which fail authentication are returned to queue

@author: Fred Williamson
'''
import logging, datetime
logging.basicConfig(filename="logs/" + str(datetime.date.today()) + ".log", encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logging.info('fylgja.main.py - Importing modules to main.py')
import queue, os, threading
logging.debug('fylgja.main.py - queue, os, threading')
import completion, authentication, utils.messages
import frontends.cli, frontends.discord
from dotenv import load_dotenv
logging.debug('fylgja.main.py - dotenv.load_dotenv')
load_dotenv()
logging.debug('fylgja.main.py - environmental variables set')
logging.info('fylgja.main.py - Modules imported')

is_running = True

def message_processor(queue: queue.Queue, authenticator, printers: dict) -> None:
    global is_running
    logging.info('fylgja.main.py - Message processor starting!')
    while is_running:
        while not queue.empty():
            next_in_queue = queue.get()
            if next_in_queue.verified != True:
                authenticator(queue, next_in_queue)
            elif next_in_queue.verified and next_in_queue.state == 0:
                completion.ChatCompletion(queue, next_in_queue)
            elif next_in_queue.verified and next_in_queue.state:
                sender = printers[next_in_queue.source]
                sender(next_in_queue)
    logging.info('fylgja.main.py - Message processor ending.')
    
def cmd_line(shell: frontends.cli.CommandLineInterface) -> None:
    global is_running
    logging.info('fylgja.main.py - Starting the command line listener!')
    while is_running:
        u_in = input("")
        if u_in != 'exit':
            shell.receive_msg(u_in)
        else:
            is_running = False
    logging.info('fylgja.main.py - Closing the command line listener.')
                
if __name__ == '__main__':
    mainq = queue.Queue()
    authenticator = authentication.CsvAuth
    
    shell = frontends.cli.CommandLineInterface(mainq)
    discord = frontends.discord.DiscoBot(mainq)
    printers = {'cmd' : shell.post_msg,
                'discord' : discord.post_msg}        
    
    processor = threading.Thread(target=message_processor, args=[mainq, authenticator, printers])
    shell_run = threading.Thread(target=cmd_line, args=[shell])
        
    processor.start()
    shell_run.start()
    discord.run_bot()