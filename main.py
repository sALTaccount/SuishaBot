import argparse
import os

import dotenv

from src import LoadDistributionManager, PermissionsManager, SuishaBot

parser = argparse.ArgumentParser(
    prog='Suisha Bot'
)
parser.add_argument('--config_path')
args = parser.parse_args()

config_path = args.config_path if args.config_path else 'config.toml'
config = SuishaBot.Config(config_path)

ips = config.config['webui_ips'].items()
ips = [ip[1] for ip in ips]
load_distributor = LoadDistributionManager.LoadDist(ips, config)

perm_manager = PermissionsManager.Permissions(config)

dotenv.load_dotenv()
token = str(os.getenv('TOKEN'))

bot = SuishaBot.Bot(token, config, load_distributor, perm_manager)
