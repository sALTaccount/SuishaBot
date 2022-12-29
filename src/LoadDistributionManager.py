import base64
import io
import time
import traceback
import json
from enum import Enum
from collections import deque
from threading import Thread

import discord

from src import AutoWebUi


def _worker(queue, ip, config):
    webui = AutoWebUi.WebUi(ip)
    while True:
        if queue:
            try:
                start_time = time.time()
                queue_obj = queue.popleft()
                response = webui.txt_to_img(queue_obj)
                embed = discord.Embed()
                params = response['parameters']
                embed.add_field(name='Prompt', value=params['prompt'])
                embed.add_field(name='Negative Prompt', value=params['negative_prompt'])
                embed.add_field(name='Steps', value=params['steps'])
                if params['height'] != config.config['command_params']['default_height']:
                    embed.add_field(name='CFG Scale', value=params['cfg_scale'])
                if params['width'] != config.config['command_params']['default_width']:
                    embed.add_field(name='CFG Scale', value=params['cfg_scale'])
                embed.add_field(name='Sampler', value=params['sampler_index'])
                embed.add_field(name='Seed', value=json.loads(response['info'])['seed'])
                if params['cfg_scale'] != config.config['command_params']['default_cfg']:
                    embed.add_field(name='CFG Scale', value=params['cfg_scale'])
                if params['enable_hr']:
                    embed.add_field(name='Highres Fix', value='True')
                if queue_obj.ctx.author.avatar is None:
                    embed.set_footer(
                        text=f'{queue_obj.ctx.author.name}#{queue_obj.ctx.author.discriminator}'
                             f'   |   compute used: {time.time() - start_time:.2f} seconds'
                             f'   |   react with ❌ to delete'
                    )
                else:
                    embed.set_footer(
                        text=f'{queue_obj.ctx.author.name}#{queue_obj.ctx.author.discriminator}'
                             f'   |   compute used: {time.time() - start_time:.2f} seconds'
                             f'   |   react with ❌ to delete',
                        icon_url=queue_obj.ctx.author.avatar.url
                    )
                image = None
                for i in response['images']:
                    image = io.BytesIO(base64.b64decode(i.split(",", 1)[0]))
                queue_obj.event_loop.create_task(queue_obj.ctx.channel.send(
                    content=f'<@{queue_obj.ctx.author.id}>',
                    file=discord.File(fp=image, filename='image.png'),
                    embed=embed
                ))
            except:
                tb = traceback.format_exc()
                # check if the queue object was retrieved before the error
                if 'queue_obj' in locals():
                    embed = discord.Embed(title='Encountered an error: ',
                                          description=str(tb),
                                          color=0xff0000)
                    # send the error to the user who requested the command that errored
                    queue_obj.event_loop.create_task(queue_obj.ctx.channel.send(embed=embed))
                else:
                    # otherwise print to console
                    print(tb)

        time.sleep(1)


class Status(Enum):
    QUEUED = 0
    IN_QUEUE = 2


class LoadDist:
    def __init__(self, ips, config):
        self.instances = []
        self.queue = deque()
        self.config = config
        for ip in ips:
            self.instances.append(Thread(target=_worker, args=(self.queue, ip, self.config)))
        for instance in self.instances:
            instance.start()

    def add_to_queue(self, queue_obj):
        try:
            status = (Status.QUEUED, len(self.queue))
            for i, queued_obj in enumerate(self.queue):
                if queued_obj.ctx.author.id == queue_obj.ctx.author.id:
                    status = (Status.IN_QUEUE, i)
            if status[0] != Status.IN_QUEUE:
                self.queue.append(queue_obj)
            return status
        except:
            return traceback.format_exc(), None
