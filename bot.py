import asyncio
import os
import message as m
import pickle

import discord
from dotenv import load_dotenv


def message_type(msg):
    if "play update" in msg.content.lower():
        return "update"
    elif "new play" in msg.content.lower():
        return "start"
    elif "play close" in msg.content.lower():
        return "close"
    else:
        return "ERROR: Type of message not specified"


def get_role_name(msg):
    if "@" in msg.content:
        return msg.content[msg.content.find("@") + 1:].split()[0][1:-1]
    else:
        return "ERROR: Role not found"


async def process_message(msg, active_strategies, guild):

    if msg.author.top_role.id != int(os.getenv('ADMIN_ROLE')) and msg.author.top_role.id != int(os.getenv('OWNER_ROLE')):
        return "not owner"
    if any(strategy.contains(msg) for strategy in active_strategies.values()):
        return "already covered"

    msg_type = message_type(msg)
    strat_id = get_role_name(msg)

    if strat_id == "ERROR: Role not found":
        return strat_id

    if msg_type == "start":
        # create new role
        await guild.create_role(name=strat_id)
        # get full role object
        role = discord.utils.get(guild.roles, name=strat_id)
        # create strategy container
        strat = m.Strategy(id=strat_id, role=role, messages=[msg], status="active", users_reacted=[])
        # add strategy to active strategies
        active_strategies[strat_id] = strat
    elif msg_type == "update":
        active_strategies[strat_id].add_message(msg)
    elif msg_type == "close":
        # take strategy out of the list of active strategies
        closed_strat = active_strategies.pop(strat_id)
        role_to_remove = closed_strat.role
        await role_to_remove.delete(reason="Strategy closed")
        print("Role: " + strat_id + " Has been removed")
    return "message successfully processed"


if __name__ == '__main__':

    strategy_filename = "active_strategies.txt"
    try:
        strat_file = open(strategy_filename, 'rb')
        active_strategies = pickle.load(strat_file)
    except FileNotFoundError:
        active_strategies = {}
    else:
        strat_file.close()

    last_msg_filename = "last_message.txt"

    try:
        msg_file = open(last_msg_filename, 'rb')
        last_message = pickle.load(msg_file)
    except FileNotFoundError:
        last_message = None
    else:
        msg_file.close()

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD = os.getenv('DISCORD_GUILD')
    print(TOKEN)

    client = discord.Client()


    @client.event
    async def on_ready():
        for guild in client.guilds:
            print(
                f'{client.user} is connected to the following guild:\n'
                f'{guild.name}(id: {guild.id})'
            )

        # Activity name (mostly for shits and giggles, doesn't really do much but it's fun code)
        activity = discord.Game(name="Just testing some new features!")
        await client.change_presence(status=discord.Status.idle, activity=activity)
        '''
        member_ids = '\n - '.join([str(member.id) + ": " + member.name for member in guild.members])
        print(f'Guild Members:\n - {member_ids}')
        '''
        '''
        # constantly check for reactions to messages in the channel
        def check(reaction, user):
            return str(reaction.emoji) is not None

        reacted = False
        while not reacted:
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=1.0, check=check)
            except asyncio.TimeoutError:
                continue
            else:
                await channel.send('👍')
                reacted = True
        '''

    @client.event
    async def on_message(message):
        channel = message.channel
        content = message.content


        if channel.name == "bot_test":
            flag = await process_message(message, active_strategies, client.guilds[0])
            print(flag)



    client.run(TOKEN)
