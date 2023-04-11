import asyncio
from abc import ABC
from typing import Optional
import string

import toml
import discord
from discord import option

from src import AutoWebUi
from src.LoadDistributionManager import Status


class Config:
    def __init__(self, config_path):
        self.config = toml.load(config_path)


class Bot:
    def __init__(self, token, config, load_distributor, perm_manager, **options):
        super().__init__(**options)
        self.load_distributor = load_distributor
        self.perm_manager = perm_manager
        instance = Suisha(activity=discord.Activity(name='Dr', type=discord.ActivityType.custom))

        @instance.event
        async def on_ready():
            print(f'{instance.user} online')

        params = config.config['command_params']

        def stringify(queue_obj):
            maps = {
                'prompt': ('prompt', None),
                'negative_prompt': ('negative_prompt', params['default_negative']),
                'steps': ('steps', params['default_steps']),
                'width': ('width', params['default_width']) ,
                'height': ('height', params['default_height']),
                'seed': ('seed', -1),
                'cfg_scale': ('guidance_scale', params['default_cfg']),
                'sampler_index': ('sampler', params['default_sampler']),
                'enable_hr': ('highres_fix', False)
            }
            cmd_parts = ['/dream']
            for item in queue_obj.args.items():
                if item[0] in maps:
                    # don't append if value is default
                    if item[1] != maps[item[0]][1]:
                        cmd_parts.append(f'{maps[item[0]][0]}: {item[1]}')
            return ' '.join(cmd_parts)

        @instance.slash_command(name="model", description="switch model")
        @option('model', str, description='model to switch to', required=True)
        async def model(ctx, *, model: str):
            webui = AutoWebUi.WebUi("http://127.0.0.1:7860/")
            print(f'Request -- {ctx.author.name}#{ctx.author.discriminator} -- change model to {model}')
            queue_obj = AutoWebUi.QueueObj(
                event_loop=asyncio.get_event_loop(),
                ctx=ctx,
                args={
                    'sd_model_checkpoint': model
                }
            )
            response, status_code = webui.switch_model(queue_obj)
            if status_code != 200:
                await ctx.respond("shits fucked")
            else:
                await ctx.respond(response)

        @instance.slash_command(name="dream", description="Generate an image")
        @option('prompt', str, description='The prompt for generating the image', required=True)
        @option('negative_prompt', str, description='', required=False)
        @option('height', int, description='Image Height', required=False,
                choices=[x for x in range(params['min_height'], params['max_height'] + 64, 64)])
        @option('width', int, description='Image Width', required=False,
                choices=[x for x in range(params['min_width'], params['max_width'] + 64, 64)])
        @option('steps', int, description='Sampling Steps', required=False,
                choices=[x for x in
                         range(params['min_steps'], params['max_steps'] + params['step_step'], params['step_step'])])
        @option('seed', int, description='Image seed', required=False)
        @option('guidance_scale', float, description='CFG scale', required=False)
        @option('sampler', str, description='Sampling method', required=False, choices=params['samplers'])
        @option('highres_fix', bool, description='Highres Image Fix', required=False)
        async def generate(ctx, *, prompt: str,
                           negative_prompt: Optional[str] = params['default_negative'],
                           height: Optional[int] = params['default_height'],
                           width: Optional[int] = params['default_width'],
                           steps: Optional[int] = params['default_steps'],
                           seed: Optional[int] = -1,
                           guidance_scale: Optional[float] = params['default_cfg'],
                           sampler: Optional[str] = params['default_sampler'],
                           highres_fix: Optional[bool] = False):
            # Check DM access perms
            if ctx.channel.type.name == 'private':
                perm_manager.can_dm(ctx.author)
                embed = discord.Embed(title='DM Access Disabled',
                                      description=f'You do not have permission to DM the bot',
                                      color=0xEECCAA)
                await ctx.respond(embed=embed, ephemeral=True)
                return
            # Check for banned words
            search = prompt if config.config['blacklist']['allow_in_negative'] else ' '.join([prompt, negative_prompt])
            for word in config.config['blacklist']['words']:
                # remove punctuation from the prompt before searching
                for word2 in search.translate(str.maketrans('', '', string.punctuation)).split():
                    if word.lower() == word2.lower():
                        print(f'Denied -- {ctx.author.name}#{ctx.author.discriminator} tried to use banned word {word}!')
                        await ctx.respond(f'You tried to use a banned word! ({word})', ephemeral=True)
                        return
            # Process request
            print(f'Request -- {ctx.author.name}#{ctx.author.discriminator} -- Prompt: {prompt}')
            queue_obj = AutoWebUi.QueueObj(
                event_loop=asyncio.get_event_loop(),
                ctx=ctx,
                args={
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'steps': steps,
                    'width': width,
                    'height': height,
                    'seed': seed,
                    'cfg_scale': guidance_scale,
                    'sampler_index': sampler,
                    'enable_hr': highres_fix
                }
            )

            response, info = self.load_distributor.add_to_queue(queue_obj)

            if response == Status.QUEUED:
                await ctx.respond(
                    f'`Generating for {ctx.author.name}#{ctx.author.discriminator}` - `Queue Position: {info}` - `command: {stringify(queue_obj).replace("`", "")}`')
            elif response == Status.IN_QUEUE:
                embed = discord.Embed(title='Already in queue!',
                                      description=f'Please wait for your current image to finish generating before generating a new image\n'
                                                  f'Your position: {info + 1}',
                                      color=0xDD0000)
                await ctx.respond(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title='Encountered an error: ',
                                      description=str(response),
                                      color=0xff0000)
                await ctx.respond(embed=embed)

        instance.run(token)


class Suisha(discord.Bot, ABC):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)

    async def on_message(self, message):
        if message.channel.type.name != 'private':
            if message.author == self.user:
                try:
                    # Check if the message from Shanghai was actually a generation
                    if message.embeds[0].fields[0].name == 'Prompt':
                        await message.add_reaction('❌')
                except:
                    pass

    async def on_raw_reaction_add(self, ctx):
        if ctx.emoji.name == '❌':
            message = self.get_channel(ctx.channel_id)
            if not message:
                return
            message = await message.fetch_message(ctx.message_id)
            if message.embeds:
                # look at the message footer to see if the generation was by the user who reacted
                if f'{ctx.member.name}#{ctx.member.discriminator}' in message.embeds[0].footer.text:
                    await message.delete()
