'''
fylgja/frontends/discord.py
Copyright (c) 2023 Frederick T Williamson
'''
import logging, discord, dotenv, os, queue, asyncio, re
from utils.messages import Message
dotenv.load_dotenv()

logging.info('fylgja.frontends.discord.py - Loading frontends.discord.py')

class DiscoBot(object):
    '''
    classdocs
    '''


    def __init__(self, q: queue.Queue):
        '''
        Constructor
        '''
        logging.info('fylgja.frontends.discord.py - Instantiating a new DiscoBot object')
        self.q = q
        self.intents = discord.Intents.none()
        self.intents.dm_messages = True
        self.client = discord.Client(intents=self.intents)
        
        @self.client.event
        async def on_ready():
            logging.info('fylgja.frontends.discord.py - Successfully connected to Discord as {}'.format(self.client.user))
            
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            else:
                msg = Message('discord', message.author.id, message.clean_content)
                self.q.put(msg)
                                
    def run_bot(self) -> None:
        logging.info('fylgja.frontends.discord.py - Starting discord bot.')
        self.client.run(os.environ.get('DISCORD_API_KEY'))
        
    def post_msg(self, response: Message):
        user = asyncio.run_coroutine_threadsafe(self.client.fetch_user(response.user), self.client.loop).result()
        if len(response.chat['content']) < 1900:
            asyncio.run_coroutine_threadsafe(user.send(response.chat['content']), self.client.loop)
        else:
            split_txt = re.findall(r'(\b.{1,1900}[\.,;]? |.{1,1900}$)', response.chat['content'], flags=re.S)
            split_q = queue.Queue()
            for string in split_txt:
                split_q.put(string)
            while not split_q.empty():
                next_out = split_q.get()
                asyncio.run_coroutine_threadsafe(user.send(next_out), self.client.loop)