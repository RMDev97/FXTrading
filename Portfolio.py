from copy import deepcopy
from decimal import Decimal

from Events.OrderEvent import OrderEvent
from Position import Position


class Portfolio(object):
    def __init__(
            self, ticker, events, home_currency="GBP",
            leverage=20, equity=Decimal("100000.00"),
            risk_per_trade=Decimal("0.02")
    ):
        self.ticker = ticker
        self.events = events
        self.home_currency = home_currency
        self.leverage = leverage
        self.equity = equity
        self.balance = deepcopy(self.equity)
        self.risk_per_trade = risk_per_trade
        self.trade_units = self.calc_risk_position_size()
        self.positions = {}

    def calc_risk_position_size(self):
        return self.equity * self.risk_per_trade

    def add_new_position(
            self, position_type, currency_pair, units, ticker
    ):
        ps = Position(
            self.home_currency, position_type,
            currency_pair, units, ticker
        )
        self.positions[currency_pair] = ps

    def add_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            ps.add_units(units)
            return True

    def remove_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            pnl = ps.remove_units(units)
            self.balance += pnl
            return True

    def close_position(self, currency_pair):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            pnl = ps.close_position()
            self.balance += pnl
            del [self.positions[currency_pair]]
            return True

    def update_portfolio(self, tick_event):
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (PnL).
        """
        currency_pair = tick_event.instrument
        if currency_pair in self.positions:
            ps = self.positions[currency_pair]
            ps.update_position_price()

    def execute_signal(self, signal_event):
        # Check that the prices ticker contains all necessary currency pairs prior to executing an order
        execute = True
        tp = self.ticker.prices
        for pair in tp:
            if tp[pair]["ask"] is None or tp[pair]["bid"] is None:
                execute = False

        # All necessary pricing data is available, we can execute
        if execute:
            side = signal_event.side
            currency_pair = signal_event.instrument
            units = int(self.trade_units)

            # If there is no position, create one
            if currency_pair not in self.positions:
                if side == "buy":
                    position_type = "long"
                else:
                    position_type = "short"
                self.add_new_position(
                    position_type, currency_pair,
                    units, self.ticker
                )

            # If a position exists add or remove units
            else:
                position = self.positions[currency_pair]

                if side == "buy" and position.position_type == "long":
                    self.add_position_units(currency_pair, units)

                elif side == "sell" and position.position_type == "long":
                    if units == position.units:
                        self.close_position(currency_pair)
                    elif units < position.units:
                        self.remove_position_units(currency_pair, units)
                    elif units > position.units:
                        new_units = units - position.units
                        self.close_position(currency_pair)
                        self.add_new_position("short", currency_pair, new_units, self.ticker)

                elif side == "buy" and position.position_type == "short":
                    if units == position.units:
                        self.close_position(currency_pair)
                    elif units < position.units:
                        self.remove_position_units(currency_pair, units)
                    elif units > position.units:
                        new_units = units - position.units
                        self.close_position(currency_pair)
                        self.add_new_position("long", currency_pair, new_units, self.ticker)

                elif side == "sell" and position.position_type == "short":
                    self.add_position_units(currency_pair, units)

            order = OrderEvent("%s_%s" % (currency_pair[:3], currency_pair[3:]), units, "market", side)
            self.events.put(order)

            print("Portfolio Balance: %s" % self.balance)
        else:
            print("Unable to execute order as price data was insufficient.")
