from decimal import Decimal, getcontext, ROUND_HALF_DOWN


class Position:
    """
    A class to represent an open position of a FX trade in our internal simulation system, one class instance per
    market traded
    """

    def __init__(self, home_currency, position_type, currency_pair, units, ticker):
        """

        :param home_currency: the local currency which the balance is represented as
        :param position_type: Either "long" or "short"
        :param currency_pair: the currency pair that is being traded (e.g. EURUSD)
        :param units: the number of units held by the position
        :param ticker: the price ticker
        """
        self.ticker = ticker
        self.units = units
        self.currency_pair = currency_pair
        self.position_type = position_type
        self.home_currency = home_currency
        self.current_price = None
        self.average_price = None
        self.base_currency = None
        self.quote_currency = None
        self.quote_home_currency_pair = None

        self.setup_currencies()

        self.profit_base = self.calculate_profit_base()
        self.profit_percentage = self.calculate_profit_percentage()

    def calculate_pips(self):
        """
        Calculate the number of pips that the position has moved by since purchase
        :return:
        """
        mult = Decimal("1")
        if self.position_type == "long":
            mult = Decimal("1")
        elif self.position_type == "short":
            mult = Decimal("-1")
        pips = (mult * (self.current_price - self.average_price)).quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )
        return pips

    def calculate_profit_base(self):
        pips = self.calculate_pips()
        ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
        if self.position_type == "long":
            qh_close = ticker_qh["bid"]
        else:
            qh_close = ticker_qh["ask"]
        profit = pips * qh_close * self.units
        return profit.quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )

    def calculate_profit_percentage(self):
        return (self.profit_base / self.units * Decimal("100.00")).quantize(
            Decimal("0.00001"), ROUND_HALF_DOWN
        )

    def add_units(self, units):
        cp = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            add_price = cp["ask"]
        else:
            add_price = cp["bid"]
        new_total_units = self.units + units
        new_total_cost = self.average_price * self.units + add_price * units
        self.average_price = new_total_cost / new_total_units
        self.units = new_total_units
        self.update_position_price()

    def update_position_price(self):
        ticker_cur = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            self.current_price = Decimal(str(ticker_cur["bid"]))
        else:
            self.current_price = Decimal(str(ticker_cur["ask"]))
        self.profit_base = self.calculate_profit_base()
        self.profit_percentage = self.calculate_profit_percentage()

    def setup_currencies(self):
        self.base_currency = self.currency_pair[:3]
        self.quote_currency = self.currency_pair[3:]

        self.quote_home_currency_pair = "%s%s" % (self.quote_currency, self.home_currency)

        ticker_currency = self.ticker.prices[self.currency_pair]

        if self.position_type == "long":
            self.average_price = Decimal(str(ticker_currency["ask"]))
            self.current_price = Decimal(str(ticker_currency["bid"]))
        else:
            self.average_price = Decimal(str(ticker_currency["bid"]))
            self.current_price = Decimal(str(ticker_currency["ask"]))

    def remove_units(self, units):
        dec_units = Decimal(str(units))
        ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
        if self.position_type == "long":
            qh_close = ticker_qh["ask"]
        else:
            qh_close = ticker_qh["bid"]
        self.units -= dec_units
        self.update_position_price()
        # Calculate PnL
        pnl = self.calculate_pips() * qh_close * dec_units
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))

    def close_position(self):
        ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
        if self.position_type == "long":
            qh_close = ticker_qh["ask"]
        else:
            qh_close = ticker_qh["bid"]
        self.update_position_price()
        # Calculate PnL
        pnl = self.calculate_pips() * qh_close * self.units
        getcontext().rounding = ROUND_HALF_DOWN
        return pnl.quantize(Decimal("0.01"))
