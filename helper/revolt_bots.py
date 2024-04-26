import json

import revolt
from revoltbots import RBL

with open("json/config.json", "r") as f:
    config = json.load(f)


class RBList:
    def __init__(self, client):
        self.revolt_bot_list = RBL.RevoltBots(ApiKey=config['RBL_KEY'], botId="01FZB4GBHDVYY6KT8JH4RBX4KR")
        self.client = client

    async def get(self):
        """ GET Stats """
        res = self.revolt_bot_list.getStats()
        print(res)

    def post(self):
        """ POST Stats """
        res = requests.post(
            url="https://revoltbots.org/api/v1/bots/stats",
            headers={
                "Authorization": config['RBL_KEY'],
                "servers": str(len(self.client.servers)),
            }
        )
        if res.status_code != 200:
            print(res)

    def check_votes(self):
        """ GET Votes """
        res = self.revolt_bot_list.checkVotes()
        print(res)

    def get_voter(self, user: revolt.User):
        """ Check Voter """
        res = self.revolt_bot_list.checkVoter(userId=user.id)
        print(res)
