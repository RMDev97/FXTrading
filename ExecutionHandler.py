import json

import oandapyV20
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest


class Execution:
    def __init__(self, domain, access_token, account_id):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.api = oandapyV20.API(access_token=access_token)

    @staticmethod
    def multiplier(side):
        if side == "buy":
            return 1
        elif side == "sell":
            return -1
        else:
            return 0

    def execute_order(self, event):
        if event.order_type == "market":

            market_order = MarketOrderRequest(
                instrument=event.instrument,
                units=event.units * self.multiplier(event.side))

            r = orders.OrderCreate(self.account_id, data=market_order.data)
            try:
                # create the OrderCreate request
                rv = self.api.request(r)
            except oandapyV20.exceptions.V20Error as err:
                print(r.status_code, err)
            else:
                print(json.dumps(rv, indent=2))
        else:
            pass
