from decimal import Decimal, getcontext, ROUND_HALF_DOWN


class PriceHandler(object):
    """
    PriceHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).
    The goal of a (derived) PriceHandler object is to output a set of
    bid/ask/timestamp "ticks" for each currency pair and place them into
    an event queue.
    This will replicate how a live strategy would function as current
    tick data would be streamed via a brokerage. Thus a historic and live
    system will be treated identically by the rest of the QSForex
    backtesting suite.
    """

    def _set_up_prices_dict(self):
        """
        Due to the way that the Position object handles P&L
        calculation, it is necessary to include values for not
        only base/quote currencies but also their reciprocals.
        This means that this class will contain keys for, e.g.
        "GBPUSD" and "USDGBP".
        """
        prices_dict = {p: {"bid": None, "ask": None, "time": None} for p in self.pairs}

        inv_prices_dict = {"%s%s" % (p[3:], p[:3]): {"bid": None, "ask": None, "time": None} for p in self.pairs}

        prices_dict.update(inv_prices_dict)
        return prices_dict

    @staticmethod
    def invert_prices(pair, bid, ask):
        """
        Simply inverts the prices for a particular currency pair.
        This will turn the bid/ask of "GBPUSD" into bid/ask for
        "USDGBP" and place them in the prices dictionary.
        """
        getcontext().rounding = ROUND_HALF_DOWN
        inv_pair = "%s%s" % (pair[3:], pair[:3])
        inv_bid = (Decimal("1.0") / bid).quantize(
            Decimal("0.00001")
        )
        inv_ask = (Decimal("1.0") / ask).quantize(
            Decimal("0.00001")
        )
        return inv_pair, inv_bid, inv_ask
