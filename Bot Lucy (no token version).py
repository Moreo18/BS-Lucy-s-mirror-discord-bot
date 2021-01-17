import discord
from discord.ext import commands, menus
from Googlestuff import linkc, searchc
from asyncio import TimeoutError
from requests import get
import json


TOKEN = ''
client = commands.Bot(command_prefix='!')
channel = None


class MySource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        message1 = '\n'.join(f'`{i}. {v[0]}`' for i, v in enumerate(entries, start=offset))
        message2 = "\nYou can reply a code to have the link or type d to finish your request"
        return message1 + message2


# Change rich presence and print in console that the bot is ready
@client.event
async def on_ready():
    global channel
    channel = client.get_channel()
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


# Command to search a song and to get the link to it
@client.command(brief="Search for a map and return all the results", description="Search for a map and return all the results")
async def search(ctx, *args):
    if ctx.message.channel == channel:

        result = searchc(' '.join(args))

        if not result:
            await ctx.send(f"Nothing was found with the argument {' '.join(args)}")
        else:
            pages = menus.MenuPages(source=MySource(result), clear_reactions_after=True, delete_message_after=True)
            await pages.start(ctx)

        def check(m):
            return m.author == ctx.message.author

        msg = await client.wait_for('message', check=check, timeout=60.0)
        if msg.content.upper() == 'D':
            pages.stop()
        else:
            searchres = linkc(msg.content)
            gcm = ()
            for item in searchres:
                key = item[0].split(' ')[0]
                if msg.content == key:
                    gcm = item
                    break
            if not gcm:
                await ctx.send(f'Nothing was found with the key {msg.content}')
            else:
                embed = discord.Embed(title="Click here to download the map",
                                      url=f"https://drive.google.com/file/d/{gcm[1]}", description=gcm[0],
                                      color=0xff0080)
                await ctx.send(embed=embed)
    else:
        await client.http.delete_message(ctx.message.channel.id, ctx.message.id)


# To handle all the errors of the search command
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


# Command that give a link to a song from a bsr key
@client.command(brief="Give you the link to download the map",
                description="Give you the link to download a map, takes 1 argument : the maps key")
async def link(ctx, arg1):
    if ctx.message.channel == channel:
        searchres = linkc(arg1)
        gcm = ()
        for item in searchres:
            key = item[0].split(' ')[0]
            if arg1 == key:
                gcm = item
                break
        if not gcm:
            await ctx.send(f'Nothing was found with the key {arg1}')
        else:
            embed = discord.Embed(title="Click here to download the map",
                                  url=f"https://drive.google.com/file/d/{gcm[1]}", description=gcm[0],
                                  color=0xff0080)
            await ctx.send(embed=embed)
    else:
        await client.http.delete_message(ctx.message.channel.id, ctx.message.id)


# To handle all the errors of the link command
@link.error
async def link_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to specify a key")
    else:
        await ctx.send("Sorry, an error occurred, you can report it in the <#788827448166711356> channel")
        print(error)


# Command that give all the links to a list of maps that the user sends
@client.command(brief="list all the map you want and then, get link")
async def glink(ctx):
    if ctx.message.channel == channel:
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
                searchres = linkc(msg.content)
                gcm = ()
                for item in searchres:
                    key = item[0].split(' ')[0]
                    if msg.content == key:
                        gcm = item
                        break
                if not gcm:
                    rese.append('Not found')
                else:
                    rese.append(gcm)
        message = ''
        for item in rese:
            if item == 'Not found':
                message += f"{res[rese.index(item)]} : Not found\n"
            else:
                message += f'{item[0]} : <https://drive.google.com/file/d/{item[1]}>\n'
        await ctx.send(message)
    else:
        await client.http.delete_message(ctx.message.channel.id, ctx.message.id)


# To handle all the errors of the glink command
@glink.error
async def glink_error(ctx,error):
    error = getattr(error, "original", error)
    if isinstance(error, TimeoutError):
        await ctx.send('The request timed out\nDon\'t forget to send "d" to end your request list')
    else:
        await ctx.send("Sorry, an error occurred, you can report it in the <#788827448166711356> channel")
        print(error)


# Send in private all the links to all the song in an attached playlist
@client.command(brief='Send all the link to download an entire playlist')
async def playlist(ctx):
    if ctx.message.channel == channel:
        headers = {
            'User-Agent': 'DiscordBot/3.0'}
        url = ctx.message.attachments[0].url
        bsurl = 'https://beatsaver.com/api/maps/by-hash/'
        result = []
        req = get(url)
        jfile = json.loads(req.text)
        nbr = 0
        for item in jfile['songs']: nbr += 1
        if nbr >= 50:
            await ctx.send('Sorry, you can\'t download a playlist with more than 50 maps')
        else:
            msg = await ctx.send(f'Playlist : {jfile["playlistTitle"]}, please wait <a:loading:799952358704283658>')
            for item in jfile['songs']:
                bsreq = get(bsurl + item['hash'], headers=headers)
                bsfile = json.loads(bsreq.text)
                searchres = linkc(bsfile['key'])
                gcm = ()
                for item2 in searchres:
                    key = item2[0].split(' ')[0]
                    if bsfile['key'] == key:
                        gcm = item2
                        break
                if not gcm:
                    result.append('Not found')
                else:
                    result.append(gcm)
            message = ''
            chacount = 0
            split = False
            for item in result:
                if chacount + len(f'{item[0]} : <https://drive.google.com/file/d/{item[1]}>\n') >= 2000:
                    chacount = 0
                    message += 'ò'
                    split = True
                if item == 'Not found':
                    message += f"Not found\n"
                else:
                    chacount += len(f'{item[0]} : <https://drive.google.com/file/d/{item[1]}>\n')
                    message += f'{result.index(item) + 1}. {item[0]} : <https://drive.google.com/file/d/{item[1]}>\n'
            if split:
                messagelist = message.split('ò')
                for item in messagelist:
                    await ctx.author.send(item)
            else:
                await ctx.author.send(message)
        client.http.edit_message(msg.channel.id, msg.id,
                                 f'Playlist : {jfile["playlistTitle"]}, Delivered <a:BlobSaber:764539666686017605>')
    else:
        await client.http.delete_message(ctx.message.channel.id, ctx.message.id)


# To handle all the errors of the playlist command
@playlist.error
async def playlist_error(ctx,error):
    error = getattr(error, "original", error)
    if isinstance(error, IndexError):
        await ctx.send('You need to attach a playlist in json or bplist with your message')
    else:
        await ctx.send("Sorry, an error occurred, you can report it in the <#788827448166711356> channel")
        print(error)


client.run(TOKEN)
