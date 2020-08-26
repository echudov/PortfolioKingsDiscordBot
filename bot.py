import asyncio
import os
import message as m
import pickle
import atexit
import tkinter as tk

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
    if len(msg.role_mentions) != 0:
        return str(msg.role_mentions[0].name)
    if "@" in msg.content:
        return msg.content[msg.content.find("@") + 1:].split()[0]
    else:
        return "ERROR: Role not found"


async def process_message(msg, active_strategies, guild):
    if msg.author.top_role.id != int(os.getenv('ADMIN_ROLE')) and msg.author.top_role.id != int(
            os.getenv('OWNER_ROLE')):
        return "not owner"
    if any(strategy.contains(msg) for strategy in active_strategies.values()):
        return "already covered"

    msg_type = message_type(msg)
    strat_id = get_role_name(msg)
    print(strat_id)
    if strat_id == "ERROR: Role not found":
        return strat_id

    if msg_type == "start":
        # create new role
        await guild.create_role(name=strat_id)
        # get full role object
        role = discord.utils.get(guild.roles, name=strat_id)
        # create strategy container
        strat = m.Strategy(id=strat_id, messages=[str(msg.content)], status="active", users_reacted=[])
        # add strategy to active strategies
        active_strategies[strat_id] = strat
    elif msg_type == "update":
        active_strategies[strat_id].add_message(msg)
    elif msg_type == "close":
        # take strategy out of the list of active strategies
        active_strategies.pop(strat_id)
        role_to_remove = discord.utils.get(guild.roles, name=strat_id)
        try:
            await role_to_remove.delete(reason="Play Close")
        except discord.Forbidden:
            print("Missing Permissions to delete this role!")
        print("Role: " + strat_id + " Has been removed")
    return "message successfully processed"


def save_progress(strategies, msg, strat_filename, msg_filename):
    f = open(msg_filename, "wb")
    pickle.dump(msg, f)
    f = open(strat_filename, "wb")
    pickle.dump(strategies, f)


if __name__ == '__main__':

    strategy_filename = "active_strategies.txt"
    active_strategies = {}
    try:
        strat_file = open(strategy_filename, 'rb')
        active_strategies = pickle.load(strat_file)
    except FileNotFoundError:
        print(strategy_filename + " Not found")
    else:
        strat_file.close()

    last_msg_filename = "last_message.txt"

    last_message = [""]
    try:
        msg_file = open(last_msg_filename, 'rb')
        last_message = pickle.load(msg_file)
        if last_message is None:
            last_message = [""]
    except FileNotFoundError:
        print(last_msg_filename + " Not found")
    else:
        msg_file.close()

    def save_progress_with_names():
        print('bruh')
        save_progress(active_strategies, last_message, strategy_filename, last_msg_filename)

    atexit.register(save_progress_with_names)

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

        # constantly check for reactions to messages in the channel
        def check(reaction, user):
            return str(reaction.emoji) is not None and \
                   reaction.message.channel.name == os.getenv('OPTIONS_CHANNEL') and \
                   any(active_strat.contains(reaction.message) for active_strat in active_strategies)
        '''
        # check for reactions to messages in the channel that are in the list of current messages
        while True:
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=1.0, check=check)
            except asyncio.TimeoutError:
                continue
            else:
                print(user.name + " reacted")
                name = get_role_name(reaction.message)
                role = discord.utils.get(guild.roles, name=name)
                user.add_role(role)
                active_strategies[name].react(user)
        '''

    @client.event
    async def on_raw_reaction_add(payload):

        guild = client.guilds[0]
        emoji = payload.emoji
        member = payload.member
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        def check(message, emoji, member):
            return emoji is not None and \
                   payload.channel_id == int(os.getenv('BOT_TEST_CHANNEL_ID')) and \
                   any(active_strat.contains(message) for active_strat in active_strategies.values())
        print(member.name)
        if check(message, emoji, member):
            print(member.name + " reacted")
            print(message.content)
            name = get_role_name(message)
            print(name)
            role = discord.utils.get(client.guilds[0].roles, name=name)
            print(role.name)
            await member.add_roles(role)
            active_strategies[name].react(member)


    @client.event
    async def on_message(message):
        channel = message.channel

        if channel.name == "bot_test":
            flag = await process_message(message, active_strategies, client.guilds[0])
            if flag == "message successfully processed":
                print(active_strategies.values())
                last_message[0] = message.content
                print(last_message)
            print(flag)


    async def open_window():
        root = tk.Tk()
        frame = tk.Frame(root)
        frame.pack()

        button = tk.Button(frame, text="QUIT", fg="red", command=quit)
        button.pack()

        root.mainloop()

    client.run(TOKEN)


