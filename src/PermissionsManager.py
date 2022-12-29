import time


class Permissions:
    def __init__(self, config):
        self.roles = []
        self.all_dm = False
        self.rate_limiter = RateLimits(config)
        if 'ALL' in config.config['dm_access_roles'] and config.config['dm_access_roles']['ALL']:
            self.all_dm = True
        else:
            for role in config.config['dm_access_roles']:
                if role != 'ALL':
                    self.roles.append((role, 1))

    def can_dm(self, user):
        if self.all_dm:
            return True
        for role in self.roles:
            if role[1] >= 1:
                for role2 in user.roles:
                    if role[0].id == role2[0].id:
                        return True
        return False


class RateLimits:
    def __init__(self, config):
        self.config = config
        self.ratelimits = []

    def CheckRateLimit(self, user):
        for ratelimit in self.ratelimits:
            if ratelimit.user_id == user.id:
                return ratelimit.CheckRateLimit()
        return False

    def AddGeneration(self, user):
        for ratelimit in self.ratelimits:
            if ratelimit.user_id == user.id:
                ratelimit.AddGeneration()
                return
        self.ratelimits.append(UserRateLimit(user.id, self.GetGensPerHour(user.id)))

    def GetGensPerHour(self, roles):
        return


class UserRateLimit:
    def __init__(self, user_id, gens_per_hour):
        self.user_id = user_id
        self.gens_per_hour = gens_per_hour
        self.generations = []

    def AddGeneration(self):
        self.generations.append(time.time())

    def UpdateRatelimits(self):
        mins_ago = time.time() - (60 * 60)  # 60 = 1 min, 60 * 60 = 1 hour
        self.generations = [gen for gen in self.generations if gen > mins_ago]

    def CheckRatelimit(self):
        self.UpdateRatelimits()
        return len(self.generations) > self.gens_per_hour
