import discord
from discord.ext import commands, menus
from Googlesearch import linkc, searchc
from asyncio import TimeoutError
from difflib import get_close_matches

TOKEN = ''
client = commands.Bot(command_prefix='!')


# Menu Class for the search command
class MySource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        message1 = '\n'.join(f'`{i}. {v[0]}`' for i, v in enumerate(entries, start=offset))
        message2 = "\nYou can reply a code to have the link or type d to finish your request"
        return message1 + message2


'''When the bot is ready : 
   - It opens the channel,
   - Change the rich presence,
   - Erase the old message that says the bot is under maintenance,
   - Says in the channel that it's ready'''
@client.event
async def on_ready():
    channel = client.get_channel(788806891388141629)
    print('hello')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='des talons'))
    with open('last.txt', 'r') as f:
        e = f.read()
    e = e.replace('[', '').replace(']', '').split(',')
    await client.http.delete_message(e[0], e[1])
    perms = channel.overwrites_for(channel.guild.default_role)
    perms.send_messages = True
    await channel.set_permissions(channel.guild.default_role, overwrite=perms)
    await channel.send("The bot is back online, sorry for the trouble")

# Search command which uses the Googlesearch program
@client.command(brief="Search for a map and return all the results", description="Search for a map and return all the results, takes from 1 to 3 arguments")
async def search(ctx, arg1, arg2=None, arg3=None):
    if ctx.message.channel.id == 788806891388141629:
        if arg3 is not None:
            tosearch = f"{arg1} {arg2} {arg3}"

        elif arg3 is None and arg2 != None:
            tosearch = f"{arg1} {arg2}"

        else:
            tosearch = arg1

        result = searchc(tosearch)

        if not result:
            await ctx.send(f"Nothing was found with the argument {tosearch}")
        else:
            pages = menus.MenuPages(source=MySource(result), clear_reactions_after=True, delete_message_after=True)
            await pages.start(ctx)

        def check(m):
            return m.author == ctx.message.author

        msg = await client.wait_for('message', check=check, timeout=60.0)
        if msg.content.upper() == 'D':
            pages.stop()
        else:
            searchres = linkc(arg1)
            res = []
            for item in searchres:
                temp = item[0].split(' ')
                res.append(temp[0].replace('(', ''))
            gcm = get_close_matches(arg1, res)
            if not gcm:
                print('nope')
            else:
                ind = res.index(gcm[0])
                embed = discord.Embed(title="Click here to download the map",
                                      url=f"https://drive.google.com/file/d/{searchres[ind][1]}",
                                      description=searchres[ind][0],
                                      color=0xff0080)
                await ctx.send(embed=embed)
    else:
        client.http.delete_message(ctx.message.channel.id, ctx.message.id)

# Handle all the error that the command search can return
@search.error
async def search_error(ctx, error):
    error = getattr(error, "original", error)
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to specify something to search")

    elif isinstance(error, discord.HTTPException):
        await ctx.send("Sorry, there are too many results. Try with a more precise research.")

    elif isinstance(error, TimeoutError):
        await ctx.send("Sorry, the request timed out")

    else:
        await ctx.send("Sorry, an error occurred, you can report it in the <#788827448166711356> channel")
        print(error)

# Give the link to a song using the bsr key
@client.command(brief="Give you the link to download the map",
                description="Give you the link to download a map, takes 1 argument : the maps key")
async def link(ctx, arg1):
    if ctx.message.channel.id == 788806891388141629:
        searchres = linkc(arg1)
        res = []
        for item in searchres:
            temp = item[0].split(' ')
            res.append(temp[0].replace('(', ''))
        gcm = get_close_matches(arg1, res)
        if not gcm:
            print('nope')
        else:
            ind = res.index(gcm[0])
            embed = discord.Embed(title="Click here to download the map",
                                  url=f"https://drive.google.com/file/d/{searchres[ind][1]}",
                                  description=searchres[ind][0],
                                  color=0xff0080)
            await ctx.send(embed=embed)
    else:
        client.http.delete_message(ctx.message.channel.id, ctx.message.id)

# Handle all the errors that the command link can return
@link.error
async def link_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to specify a key")
    else:
        await ctx.send("Sorry, an error occurred, you can report it in the <#788827448166711356> channel")
        print(error)

# Give all the link to songs given by the user
@client.command(brief="list all the map you want and then, get link")
async def glink(ctx):
    if ctx.message.channel.id == 788806891388141629:
        await ctx.send('Send a message for each song you want to download and then send d to have all the links')

        def check(m):
            return m.author == ctx.author

        res = []
        rese = []
        msg = await client.wait_for('message', check=check, timeout=60.0)
        res.append(msg.content)
        while msg.content.upper() != 'd'.upper():
            msg = await client.wait_for('message', check=check, timeout=60.0)
            res.append(msg.content)
        for item in res:
            if item == 'd':
                break
            else:
                searchres = linkc(item)
                ress = []
                for item2 in searchres:
                    temp = item2[0].split(' ')
                    ress.append(temp[0].replace('(', ''))
                gcm = get_close_matches(item, ress)
                if not gcm:
                    rese.append('Not found')
                else:
                    ind = ress.index(gcm[0])
                    rese.append(searchres[ind])
        message = ''
        for item in rese:
            if item == 'Not found':
                message += f"{res[rese.index(item)]} : Not found\n"
            else:
                message += f'{item[0]} : <https://drive.google.com/file/d/{item[1]}>\n'
        await ctx.send(message)
    else:
        client.http.delete_message(ctx.message.channel.id, ctx.message.id)

# Handle all the errors that the glink command can return
@glink.error
async def glink_error(ctx,error):
    error = getattr(error, "original", error)
    if isinstance(error, TimeoutError):
        await ctx.send('The request timed out\nDon\'t forget to send "d" to end your request list')
    else:
        print(error)

# Make the bot stops and send a message to say that it's under maintenance
@client.command()
@commands.has_role('Yee')
async def stop(ctx):
    perms = ctx.channel.overwrites_for(ctx.guild.default_role)
    perms.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=perms)
    await client.http.delete_message(ctx.message.channel.id, ctx.message.id)
    msg = await ctx.send('**The Bot is under maintenance, sorry for the trouble**')
    with open("last.txt", 'w') as f:
        list = []
        list.append(msg.channel.id)
        list.append(msg.id)
        f.write(str(list))
    exit()

# Handle all the errors that the stop command can return
@stop.error
async def stop_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await client.http.delete_message(ctx.message.channel.id, ctx.message.id)
    else:
        ctx.send("Sorry, an error occurred, you can report it in the <#788827448166711356> channel")
        print(error)


client.run(TOKEN)
