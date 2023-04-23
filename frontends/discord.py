'''
fylgja/frontends/discord.py
Copyright (c) 2023 Frederick T Williamson
'''
import logging, discord, dotenv, os, queue, asyncio, re
from utils.messages import Message
from .frontends import Frontend
dotenv.load_dotenv()

logging.info(f'Loading frontends.discord.py')

class DiscoBot(Frontend):
    '''
    classdocs
    '''


    def __init__(self, q: queue.Queue):
        '''
        Constructor
        '''
        super().__init__(q)
        self.intents = discord.Intents.none()
        self.intents.dm_messages = True
        self.client = discord.Client(intents=self.intents)
        
        @self.client.event
        async def on_ready():
            logging.info(f'Successfully connected to Discord as {self.client.user}')
            
        @self.client.event
        async def on_message(message):
            if message.author == self.client.user:
                return
            else:
                self.receive_msg(message)
                
    def receive_msg(self, message) -> bool:
        try:
            msg = Message('discord', message.author.id, message.clean_content)
            self.q.put(msg)
            return True
        except:
            return False
                                
    def start(self, is_running) -> bool:
        logging.info(f'Starting discord bot.')
        if is_running:
            try:
                self.client.run(os.environ.get('DISCORD_API_KEY'))
                return True
            except:
                logging.critical(f'Discord bot failed to start.')
                return False
        else:
            return False
        
    def post_msg(self, response: Message) -> bool:
        try:
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
            return True
        except:
            return False