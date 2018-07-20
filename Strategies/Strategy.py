from Events.SignalEvent import SignalEvent
import copy


class TestStrategy(object):
    def __init__(self, pairs, events):
        self.events = events
        self.ticks = 0
        self.invested = False
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "invested": False
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pd = self.pairs_dict[event.instrument]
            if pd["ticks"] % 10 == 0:
                if not pd["invested"]:
                    signal = SignalEvent(event.instrument, "market", "buy")
                    self.events.put(signal)
                    pd["invested"] = True
                else:
                    signal = SignalEvent(event.instrument, "market", "sell")
                    self.events.put(signal)
                    pd["invested"] = False
            pd["ticks"] += 1
