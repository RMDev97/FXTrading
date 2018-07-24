import queue
import threading
import time
from decimal import Decimal

from Execution.ExecutionHandler import Execution
from Portfolio.Portfolio import Portfolio
from Strategies.Strategy import TestStrategy
from Price.StreamingPriceHandler import StreamingForexPrices
from settings import STREAM_DOMAIN, API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID

HEARTBEAT = 0.0


def trade(event_queue, trade_strategy, trade_portfolio, trade_execution):
    """
    Carries out an infinite while loop that polls the
    events queue and directs each event to either the
    strategy component of the execution handler. The
    loop will then pause for "heartbeat" seconds and
    continue.
    :param trade_portfolio:
    :param event_queue:
    :param trade_strategy:
    :param trade_execution:
    :return:
    """

    while True:
        try:
            event = event_queue.get(False)
        except queue.Empty:
            pass
        else:
            if event is not None:
                if event.type == 'TICK':
                    trade_strategy.calculate_signals(event)
                elif event.type == 'SIGNAL':
                    print("Sending signal event to portfolio handler: " + str(event))
                    trade_portfolio.execute_signal(event)
                    trade_portfolio.update_portfolio(event)
                elif event.type == 'ORDER':
                    print("Executing order event: " + str(event))
                    trade_execution.execute_order(event)
        time.sleep(HEARTBEAT)


if __name__ == "__main__":
    events = queue.Queue()

    # trading units of EUR/USD forex pair and GBP/USD
    pairs = ["EURUSD", "GBPUSD"]

    # create the OANDA market price streaming object and provide authentication information
    price_stream = StreamingForexPrices(STREAM_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID, pairs, events)

    # create the execution handler instance
    execution_handler = Execution(API_DOMAIN, ACCESS_TOKEN, ACCOUNT_ID)

    portfolio = Portfolio(price_stream, events, equity=Decimal("100113.20"), backtest=False)

    # create an instance of the Random Strategy class
    # strategy = MovingAverageCrossStrategy(pairs, events, 40, 200)
    strategy = TestStrategy(pairs, events)

    # create two separate threads, one for the infinite trading event loop and another for the price streaming
    trade_thread = threading.Thread(target=trade, args=(events, strategy, portfolio, execution_handler))
    price_stream_thread = threading.Thread(target=price_stream.stream_to_queue, args=[])

    # initiate both threads
    trade_thread.start()
    price_stream_thread.start()
