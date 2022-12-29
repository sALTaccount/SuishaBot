![img.png](images/suisha.png)

# Suisha

Suisha is a stable diffusion discord bot.
### Features
Negative prompts, prompt weighting, expanded token input, VAE support, xformers, SD 1.x and 2.x support,
highres fix support

Larges amount of customization via the config file

Blocked words list

Supports splitting queue amongst multiple GPUs. The GPUs don't have to be on the same computer or network.

Per role rate limits / per role DM access is **currently under development**.

## Setup

Install requirements

`pip install -r requirements.txt`

Suisha uses [Automatic1111's WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) as the backend.
Follow the directions on their repo for setup instructions.

Once you have WebUI set up, run `webui.sh` with the `--api` argument. You can also add other
arguments such as `--xformers` to use xformers memory efficient attention.

You can use the web ui interface that Automatic1111 provides to select the model and VAE to use.
Their repo has documentation on how to do so. I also recommend doing a test generation

Create a file called `.env` in the same folder as `main.py`. Inside the `.env` file,
create a line `TOKEN = xxxx`, where xxxx is your discord bot token.

The default `config.toml` will work if you didn't change any of the default WebUI settings. However,
if you did, you must update the config accordingly.

Now, you can run the bot

`python main.py`

### Multiple GPUs
You can change the GPU that WebUI uses with the `CUDA_VISIBLE_DEVICES` environment variable. You set this
environment variable to the GPU you want to use. You can launch an instance of WebUI on each GPU using this
environment variable. Make sure to use and change the `--port` argument so each instance binds to a different port.

Edit the `[webui_ips]` section of the `config.toml` file to include links to all of your WebUI instances.
The format is `instance_name = 'http://ip:port/'`. The instance name that you choose does not matter.

## Permissions and Rate Limits

Permissions and rate limits are planned, but not completed yet.