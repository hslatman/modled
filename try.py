import asyncio

from signals import Signal

was_triggered = Signal(arguments=['triggered'])

#loop = asyncio.get_event_loop()

class Sender(object):
    pass

class Test(object):
    def __init__(self):
        super(Test, self).__init__()

    def trigger(self):
        print('here')
        was_triggered.dispatch(sender=Sender, triggered=True)
        #loop.run_until_complete(task)

@asyncio.coroutine
def listen_trigger(sender, triggered):
    print(triggered)

was_triggered.connect(sender=Sender, receiver=listen_trigger)

t = Test()

t.trigger()

#loop.close()