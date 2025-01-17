
    

    #!./.venv/bin/python

import discord      # base discord module
import code         # code.interact
import os           # environment variables
import inspect      # call stack inspection
import random       # dumb random number generator

from discord.ext import commands    # Bot class and utils

################################################################################
############################### HELPER FUNCTIONS ###############################
################################################################################

# log_msg - fancy print
#   @msg   : string to print
#   @level : log level from {'debug', 'info', 'warning', 'error'}
def log_msg(msg: str, level: str):
    # user selectable display config (prompt symbol, color)
    dsp_sel = {
        'debug'   : ('\033[34m', '-'),
        'info'    : ('\033[32m', '*'),
        'warning' : ('\033[33m', '?'),
        'error'   : ('\033[31m', '!'),
    }

    # internal ansi codes
    _extra_ansi = {
        'critical' : '\033[35m',
        'bold'     : '\033[1m',
        'unbold'   : '\033[2m',
        'clear'    : '\033[0m',
    }

    # get information about call site
    caller = inspect.stack()[1]

    # input sanity check
    if level not in dsp_sel:
        print('%s%s[@] %s:%d %sBad log level: "%s"%s' % \
            (_extra_ansi['critical'], _extra_ansi['bold'],
             caller.function, caller.lineno,
             _extra_ansi['unbold'], level, _extra_ansi['clear']))
        return

    # print the damn message already
    print('%s%s[%s] %s:%d %s%s%s' % \
        (_extra_ansi['bold'], *dsp_sel[level],
         caller.function, caller.lineno,
         _extra_ansi['unbold'], msg, _extra_ansi['clear']))

################################################################################
############################## BOT IMPLEMENTATION ##############################
################################################################################

# bot instantiation
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# on_ready - called after connection to server is established
@bot.event
async def on_ready():
    log_msg('logged on as <%s>' % bot.user, 'info')

# on_message - called when a new message is posted to the server
#   @msg : discord.message.Message
@bot.event
async def on_message(msg):
    # filter out our own messages
    if msg.author == bot.user:
        return
    
    log_msg('message from <%s>: "%s"' % (msg.author, msg.content), 'debug')

    # overriding the default on_message handler blocks commands from executing
    # manually call the bot's command processor on given message
    await bot.process_commands(msg)

# roll - rng chat command
#   @ctx     : command invocation context
#   @max_val : upper bound for number generation (must be at least 1)
@bot.command(brief='Generate random number between 1 and <arg>')
async def roll(ctx, max_val: int):
    # argument sanity check
    if max_val < 1:
        raise Exception('argument <max_val> must be at least 1')

    await ctx.send(random.randint(1, max_val))

@bot.command(brief='Join a voice channel')
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You are not connected to a voice channel!")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(voice_channel)
    else:
        await voice_channel.connect()
    await ctx.send(f"Joined {voice_channel}!")

@bot.command(brief='Leave the voice channel')
async def leave(ctx):
    if ctx.voice_client is None:
        await ctx.send("I am not connected to any voice channel!")
        return

    await ctx.voice_client.disconnect()
    await ctx.send("Disconnected from the voice channel.")

@bot.command(brief='Play a local audio file from the songs directory')
async def play(ctx, filename: str):
    if ctx.voice_client is None:
        await ctx.send("I need to be in a voice channel to play audio. Use the !join command.")
        return

    # Ensure no other audio is playing
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    file_path = os.path.join("songs", filename)

    # Attempt to play the audio file
    if not os.path.exists(file_path):
        await ctx.send(f"File '{filename}' not found in the 'songs' directory.")
        return

    try:
        ctx.voice_client.play(discord.FFmpegPCMAudio(source=file_path))
        await ctx.send(f"Now playing: {filename}")
    except Exception as e:
        await ctx.send(f"Error playing file: {e}")

@bot.command(brief='List all available MP3 files in the songs directory')
async def list(ctx):
    try:
        files = [f for f in os.listdir('songs') if f.endswith('.mp3')]
        if files:
            await ctx.send("Available songs:\n" + "\n".join(files))
        else:
            await ctx.send("No MP3 files found in the 'songs' directory.")
    except Exception as e:
        await ctx.send(f"Error listing files: {e}")

@bot.command(brief='Immediately disconnect from the voice channel')
async def scram(ctx):
    if ctx.voice_client is None:
        await ctx.send("I am not connected to any voice channel!")
        return

    await ctx.voice_client.disconnect()
    await ctx.send("Scrammed from the voice channel.")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot and member.voice is not None and member.voice.channel is not None:
        voice_channel = member.voice.channel
        if len(voice_channel.members) == 1:  # Bot is alone
            await member.guild.voice_client.disconnect()


# roll_error - error handler for the <roll> command
#   @ctx     : command that crashed invocation context
#   @error   : ...
@roll.error
async def roll_error(ctx, error):
    await ctx.send(str(error))

################################################################################
############################# PROGRAM ENTRY POINT ##############################
################################################################################

if __name__ == '__main__':
    # check that token exists in environment
    if 'BOT_TOKEN' not in os.environ:
        log_msg('save your token in the BOT_TOKEN env variable!', 'error')
        exit(-1)

    # launch bot (blocking operation)
    bot.run(os.environ['BOT_TOKEN'])
