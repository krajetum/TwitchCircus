import obspython as obs
import math, time
from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.type import AuthScope
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import ChannelChatMessageEvent
from twitchAPI.eventsub.websocket import EventSubWebsocket
import asyncio
from pprint import pprint
from uuid import UUID

APP_ID = '215cp2aj2rcd6bxo5fihssgadj6rxc'
APP_SECRET = '3bpbr0af6b4kxu90v06cifqk82sxsq'
USER_SCOPE = [AuthScope.CHANNEL_READ_REDEMPTIONS, AuthScope.CHANNEL_MANAGE_REDEMPTIONS, AuthScope.USER_READ_CHAT]
TARGET_CHANNEL = 'krajetum'

pub_sub = None
twitch = None
eventsub = None

def script_description():
    return """Script for simple integration with Twitch."""

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "channel", "Twitch Channel", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "app_id", "Twitch App ID", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "app_secret", "Twitch App Secret", obs.OBS_TEXT_DEFAULT)
    return props

async def on_redeem(UUID, data):
    if data['user_input']:
        message = data['user_input']
    else:
        message = 'Reward redeemed!'
    # Display the message on the screen
    # Optionally, you can also log the message to the console
    print(f"Redeemed: {message}")
    
async def on_message(data: ChannelChatMessageEvent):

    print(f"Message from {data.event.chatter_user_name}")



async def load(settings):
    #global pub_sub
    try:
        global eventsub
        global twitch
        global pub_sub
        
        app_id = obs.obs_data_get_string(settings, "app_id")
        app_secret = obs.obs_data_get_string(settings, "app_secret")
        channel = obs.obs_data_get_string(settings, "channel")
        if not app_id or not app_secret or not channel: 
            print("App ID, App Secret, and Channel are required.")
            return
        
        
        twitch = Twitch(app_id, app_secret)
        
        #await setup_twitch_pubsub(twitch)
        await set_up_eventsub_client(twitch)
        user = await first(twitch.get_users(logins=[channel]))
        if not user:
            print(f"User {channel} not found")
            return
        
        await eventsub.listen_channel_chat_message(user.id, user.id, on_message)
        #await pub_sub.listen_channel_points(user.id, on_redeem)
    except Exception as e:
        print(f"Error: {e}")
        

async def set_up_eventsub_client(twitch: Twitch):
    global eventsub
    
    helper = UserAuthenticationStorageHelper(twitch, USER_SCOPE)
    await helper.bind()
    # create eventsub websocket instance and start the client.
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

async def setup_twitch_pubsub(twitch: Twitch):
    global pub_sub

    auth = UserAuthenticator(twitch, USER_SCOPE, force_verify=False, url='http://localhost:17563')
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token=refresh_token)
    pub_sub = PubSub(twitch)
    pub_sub.start()


async def unload():
    global pub_sub
    global eventsub
    global twitch
    if pub_sub:
        pub_sub.stop()
    if eventsub:
        await eventsub.stop()
        
    await twitch.close()
    
def script_load(settings):
    asyncio.run(load(settings))
    
def script_unload():
    global pub_sub
    global eventsub
    global twitch
    if pub_sub or eventsub:
        asyncio.run(unload())
        pub_sub = None
        eventsub = None
        twitch = None

    
    
   
    
    