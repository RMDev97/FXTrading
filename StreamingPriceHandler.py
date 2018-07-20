import requests
import json
from decimal import Decimal, getcontext, ROUND_HALF_DOWN

from Events.TickEvent import TickEvent
from PriceHandler import PriceHandler


class StreamingForexPrices(PriceHandler):
    def __init__(
            self, domain, access_token,
            account_id, pairs, events_queue
    ):
        self.domain = domain
        self.access_token = access_token
        self.account_id = account_id
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()
        self.events_queue = events_queue

    def connect_to_stream(self):
        global stream
        pairs_oanda = ["%s_%s" % (p[:3], p[3:]) for p in self.pairs]
        instruments = ",".join(pairs_oanda)
        try:
            stream = requests.Session()
            url = "https://" + self.domain + "/v3/accounts/" + str(self.account_id) + "/pricing/stream"
            headers = {'Authorization': 'Bearer ' + self.access_token}
            params = {'instruments': instruments, 'accountId': self.account_id}
            req = requests.Request('GET', url, headers=headers, params=params)
            pre = req.prepare()
            resp = stream.send(pre, stream=True, verify=False)
            return resp
        except Exception as e:
            stream.close()
            print("Caught exception when connecting to oanda price stream\n" + str(e))

    def invert_prices(self, pair, bid, ask):
        """
        Simply inverts the prices for a particular currency pair.
        This will turn the bid/ask of "GBPUSD" into bid/ask for
        "USDGBP" and place them in the prices dictionary.
        """
        getcontext().rounding = ROUND_HALF_DOWN
        inv_pair = "%s%s" % (pair[3:], pair[:3])
        inv_bid = (Decimal("1.0")/bid).quantize(
            Decimal("0.00001")
        )
        inv_ask = (Decimal("1.0")/ask).quantize(
            Decimal("0.00001")
        )
        return inv_pair, inv_bid, inv_ask

    def stream_to_queue(self):
        response = self.connect_to_stream()
        if response.status_code != 200:
            return
        for line in response.iter_lines(1):
            if line:
                try:
                    message = json.loads(line)
                    print(message)
                except Exception as e:
                    print("Caught exception when converting message into json\n" + str(e))
                    return
                if "instrument" in message or "tick" in message:
                    getcontext().rounding = ROUND_HALF_DOWN
                    instrument = message["instrument"].replace("_", "")
                    time = message["time"]
                    bid = Decimal(message["bids"][0]["price"]).quantize(
                        Decimal("0.00001")
                    )
                    ask = Decimal(message["asks"][0]["price"]).quantize(
                        Decimal("0.00001")
                    )
                    self.prices[instrument]["bid"] = bid
                    self.prices[instrument]["ask"] = ask

                    # Invert the prices (GBP_USD -> USD_GBP)
                    inv_pair, inv_bid, inv_ask = self.invert_prices(instrument, bid, ask)
                    self.prices[inv_pair]["bid"] = inv_bid
                    self.prices[inv_pair]["ask"] = inv_ask
                    self.prices[inv_pair]["time"] = time
                    tick_event = TickEvent(instrument, time, bid, ask)
                    self.events_queue.put(tick_event)
