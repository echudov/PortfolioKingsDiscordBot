import os
import message as m
import pickle
import atexit
import tkinter as tk

import discord
from dotenv import load_dotenv


def message_type(msg):
    """
    Gets the type of the play message
    :param msg: Discord message
    :return: string detailing the type of play
    """
    if "play update" in msg.content.lower():
        return "update"
    elif "new play" in msg.content.lower():
        return "start"
    elif "play close" in msg.content.lower():
        return "close"
    else:
        return "ERROR: Type of message not specified"


def get_role_name(msg):
    """
    Gets the first role's name
    :param msg: Discord message
    :return: role name
    """
    if len(msg.role_mentions) != 0:
        return str(msg.role_mentions[0].name)
    if "@" in msg.content:
        return msg.content[msg.content.find("@") + 1:].split()[0]
    else:
        return "ERROR: Role not found"


async def process_message(msg, active_strategies, guild):
    """
    Processes the message, deals with any kind of role creation/deletion, and checks to see all valid conditions
    to make the message approved for the specific channel.  Adds the message to the active strategies/
    deletes strategy as needed.
    :param msg: Discord message
    :param active_strategies: dictionary of active strategies
    :param guild: Discord guild object
    :return: flag detailing success/failure
    """
    # Checks if an admin made the message
    if msg.author.top_role.id != int(os.getenv('ADMIN_ROLE')) and msg.author.top_role.id != int(
            os.getenv('OWNER_ROLE')):
        return "not owner"

    # Checks if the message has already been seen
    if any(strategy.contains(msg) for strategy in active_strategies.values()):
        return "already covered"

    msg_type = message_type(msg)
    strat_id = get_role_name(msg)
    if strat_id == "ERROR: Role not found":
        return strat_id

    # checks all types of messages and does necessary role creation/bookkeeping
    if msg_type == "start":
        # create new role
        await guild.create_role(name=strat_id)
        # get full role object
        role = discord.utils.get(guild.roles, name=strat_id)
        # create strategy container
        strat = m.Strategy(id_number=strat_id, messages=[str(msg.content)], status="active", users_reacted=[])
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
    else:
        return "message invalid"
    return "message successfully processed"


async def check_and_process_new_messages(last_msg, active_strategies, guild, channel_name='BOT_TEST_CHANNEL_ID', limit=20):
    """
    Checks recent message history, processes messages and their reactions, and gets up to date.  All based on the last message seen.
    :param last_msg: last message seen before bot went offline
    :param active_strategies: dictionary of all active strategies
    :param guild: guild context to search for the channel
    :param channel_name: which channel to check for messages
    :return: nothing
    """
    # gets all of the necessary messages
    channel = guild.get_channel(int(os.getenv(channel_name)))
    messages = await channel.history(limit=limit, oldest_first=False).flatten()
    messages = list(reversed(messages))
    last_seen = False
    # iterates through all of the messages
    for message in messages:
        print(message.content)
        # checks to see if the iterator has gotten to the last seen message, if so, it moves on to the next and
        # actually starts processing the messages
        if not last_seen:
            if str(message.content) == last_msg:
                last_seen = True
        # starts processing messages
        else:
            # process message
            flag = await process_message(message, active_strategies, guild)
            if flag == "message successfully processed":
                print(active_strategies.values())
                last_message[0] = message.content
            print(flag)

            # check for reactions and add roles
            def check(message, reaction):
                return reaction.emoji is not None and \
                       any(active_strat.contains(message) for active_strat in active_strategies.values())

            # loop through all of the reactions in the message, and all the users with that reaction.
            for reaction in message.reactions:
                if check(message, reaction):
                    users = await reaction.users().flatten()
                    for user in users:
                        print(user.name + " reacted")
                        print("They reacted to: " + message.content)
                        name = get_role_name(message)
                        print("Role in message: " + name)
                        role = discord.utils.get(client.guilds[0].roles, name=name)
                        await user.add_roles(role)
                        print("Added role")
                        active_strategies[name].react(user)


def save_progress(strategies, msg, strat_filename, msg_filename):
    """
    Dumps the current strategies and last message into pickle files
    :param strategies: active strategies dictionary
    :param msg: last message array with single string
    :param strat_filename: as name implies
    :param msg_filename: as name implies
    """
    f = open(msg_filename, "wb")
    pickle.dump(msg, f)
    f = open(strat_filename, "wb")
    pickle.dump(strategies, f)


if __name__ == '__main__':

    # looks for all the active strategies in the strategies file
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
    # looks for the last message in the last message file
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

    # atexit function to save the progress.  Might need to implement a checker to find exit in the terminal
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
        activity = discord.Game(name="Making phat stacks")
        await client.change_presence(status=discord.Status.idle, activity=activity)

        if last_message[0] != "":
            await check_and_process_new_messages(last_message[0], active_strategies, guild, channel_name='BOT_TEST_CHANNEL_ID')


    @client.event
    async def on_raw_reaction_add(payload):
        """
        Run whenever there is a reaction added anywhere.  Checks to see if it's in a channel we care about,
        if its a message we care about, and does the necessary user processing.
        :param payload: RawReactionActionEvent object containing relevant info
        :return: nothing
        """
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
            print("They reacted to: " + message.content)
            name = get_role_name(message)
            print("Role in message: " + name)
            role = discord.utils.get(client.guilds[0].roles, name=name)
            await member.add_roles(role)
            print("Added role")
            active_strategies[name].react(member)


    @client.event
    async def on_raw_reaction_remove(payload):
        """
        Run whenever there is a reaction removed anywhere.  Checks to see if it's in a channel we care about,
        if its a message we care about, and does the necessary user processing.
        :param payload: RawReactionActionEvent object containing relevant info
        :return: nothing
        """
        guild = client.guilds[0]
        emoji = payload.emoji
        user = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        def check(message):
            return payload.channel_id == int(os.getenv('BOT_TEST_CHANNEL_ID')) and \
                   any(active_strat.contains(message) for active_strat in active_strategies.values())

        if check(message):
            print(user.name + " Removed Reaction")
            print("They removed their reaction to: " + message.content)
            name = get_role_name(message)
            print("Role in message: " + name)
            role = discord.utils.get(client.guilds[0].roles, name=name)
            await user.remove_roles(role)
            print("Removed role")
            active_strategies[name].react(user)


    @client.event
    async def on_message(message):
        channel = message.channel

        if channel.name == "bot_test":
            flag = await process_message(message, active_strategies, client.guilds[0])
            if flag == "message successfully processed":
                print(active_strategies.values())
                last_message[0] = message.content
            print(flag)


    '''
    Not exactly necessary.  If sam wants this I can try to implement this too, but it relies on a constantly running
    process which interferes with discord's.  Multithreading doesn't work for this either unfortunately, so we might
    be shit out of luck :o
    '''
    async def open_window():
        root = tk.Tk()
        frame = tk.Frame(root)
        frame.pack()

        button = tk.Button(frame, text="QUIT", fg="red", command=quit)
        button.pack()

        root.mainloop()


    client.run(TOKEN)
