from Events.Event import Event


class SignalEvent(Event):
    def __init__(self, instrument, order_type, side):
        self.type = 'SIGNAL'
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
