from threading import Thread, Condition
from kctl.logger import KctlLogger
from kctl.cli import get_args
from random import randint
from queue import Queue
import functools
import pika


EXCHANGE = 'nyse'
RECONNECT_DELAY = 5000  # 5 sec
PROPS = pika.BasicProperties(delivery_mode=2)  # persistent


class ReprClassName:
    def __repr__(self):
        return self.__class__.__name__


class ActivatingContainer:
    """Class that holds a number of other classes.
    Class names are designated in __names__

    When initialized, the container sets
    __active__ (boolean) to each subclass depending on whether
    the class is in active_names then initializes them
    with *args and **kwargs.

    Also sets the container __active__ to true if any
    children are active...

    Also stores a reference to each active subclass.
    """

    __names__ = []
    __active__ = False
    __activerefs__ = []

    def __init__(self, active_names, *args, **kwargs):
        for cls in list(self):
            cls_name = cls.__name__
            __active__ = True if cls_name in active_names else False
            setattr(cls, '__active__', __active__)

            instance = cls(*args, **kwargs)
            setattr(self, cls_name, instance)

            if __active__:
                self.__active__ = True
                self.__activerefs__.append(instance)

    def __iter__(self):
        attrs = []

        for name in self.__names__:
            attrs.append(getattr(self, name))

        return iter(attrs)

    def __len__(self):
        return len(self.__names__)

    def randomactive(self):
        rand_int = randint(0, len(self.__activerefs__) - 1)
        return self.__activerefs__[rand_int]


class Pipeline(ReprClassName):
    """The pipeline object holds services (.Services), connection
    parameters (.Connections), and command line arguments (.args)

    :param package: __package__ parameter
    :param prefetch: (from pika) Specifies a prefetch window in terms of whole
        messages. This field may be used in combination with the
        prefetch-size field; a message will only be sent in advance
        if both prefetch windows (and those at the channel and connection
        level) allow it. The prefetch-count is ignored by consumers
        who have enabled the no-ack option.
    """

    class Connections(ActivatingContainer):
        pass

    class Services(ActivatingContainer):
        pass

    def __init__(self, package, prefetch=1):
        print(f'Initializing "{repr(self)}"...')

        # predicts the active service from file path
        self.args = get_args()
        self.prefetch = prefetch

        active_connection_name = self.args.connection
        self.Connections = self.Connections([active_connection_name])
        self.active_connection = getattr(self.Connections, active_connection_name)

        if package is None:
            active_service_name = None
            self.active_service = None
        else:
            active_service_name = package.split('.')[-1]

        if self.args.debug:
            print(f'Initializing {self}.Services')

        # init services with reference to pipeline
        self.Services = self.Services([active_service_name], self)

        if package is not None:
            self.active_service = getattr(self.Services, active_service_name)
            KctlLogger.init()

        # set stub with refs to each other
        for Service in self.Services:
            for Stub in Service.Stubs:
                Stub.set_out_stub()


class Connection(ReprClassName):
    pass


class Service(ReprClassName):
    """The pipeline object holds stubs (.Stubs)

    :param _pipe: Pipeline object reference
    """
    __active__ = False

    class Stubs(ActivatingContainer):
        pass

    def __init__(self, _pipe):
        if _pipe.args.debug:
            print(f'Initializing "{self}" service...')

        self._pipe = _pipe
        active_stub_names = self.Stubs.__names__ if self.__active__ else []

        # init stubs with reference to pipeline and service
        self.Stubs = self.Stubs(active_stub_names, _pipe, self)

    def run(self):
        for Stub in self.Stubs:
            Stub.run()
        for Stub in self.Stubs:
            Stub.join()


class Stub(ReprClassName):
    __active__ = False
    _out_stub = None
    _OutStub = None
    _in_proto = None
    _InProto = None
    _out_proto = None
    _OutProto = None
    _should_send = False

    _publisher = None
    _consumer = None
    _queue = Queue()

    run_threads = []
    process_thread = None

    def __init__(self, _pipe, _service):
        if _pipe.args.debug:
            print(f'Initializing "{self}" stub...')

        self._name = repr(self)
        self._pipe = _pipe
        self._service = _service

    def __call__(self, func):
        if not self.__active__:
            self.raise_not_active()

        self.func = func

    class NotInActiveServiceError(Exception):
        pass

    class NoReturnError(Exception):
        pass

    class ShouldNotReturnError(Exception):
        pass

    class WrongMessageTypeError(Exception):
        pass

    class StubNotFoundError(Exception):
        pass

    def raise_wrong_msg_type(self, incorrect_type):
        msg = (f'"{repr(self)}" sending "{incorrect_type}" message,'
               f'but {repr(self._OutStub)} expects "{self._OutStub._in_proto}" message')
        raise self.WrongMessageTypeError(msg)

    def raise_stub_not_found(self):
        msg = f'{repr(self)} could not find "{self._out_stub}" stub to send to'
        raise self.StubNotFoundError(msg)

    def raise_not_active(self):
        # if the parent service is not active then crash
        msg = (f'Cannot use stubs from "{repr(self._service)}"'
               f'service in "{self._pipe.active}" service')
        raise self.NotInActiveServiceError(msg)

    def raise_no_return(self):
        msg = (f'"{self._name}" stub did not return anything,'
               f'but it should be sending to "{repr(self._out_stub)}" stub')
        raise self.NoReturnError(msg)

    def raise_should_not_return(self):
        msg = f'"{self._name}" stub should not return anything...'
        raise self.ShouldNotReturnError(msg)

    def set_out_stub(self):
        if self._out_stub is not None:

            for Service in self._pipe.Services:
                for Stub in Service.Stubs:
                    if repr(Stub) == self._out_stub:
                        self._OutStub = Stub

            self._should_send = True

            if self._OutStub is None:
                self.raise_stub_not_found()

            if self._out_proto != self._OutStub._in_proto:
                self.raise_wrong_msg_type(self._out_proto)

    def process(self, proto):
        debug = self._pipe.args.debug
        if debug:
            print(f'"{self}" stub processing "{proto.__class__.__name__}"...')

        returned = self.func(proto)

        if debug:
            print(f'"{self.func.__name__}" returned "{returned.__class__.__name__}"...')

        if self._should_send:
            if returned is None:
                self.raise_no_return()

            else:
                self.send(returned)

        else:
            if returned is not None:
                self.raise_should_not_return()

    def send(self, proto):

        if self._pipe.args.debug:
            not_ = '' if self.__active__ else 'not '
            print(f'"{self}" is {not_}active...')

        if self.__active__:
            self._queue.put((proto, True))

        # if the stub is not in the current service then send to it
        else:
            # if stub is not active then find a random
            stub = self._pipe.active_service.Stubs.randomactive()
            stub._queue.put((proto, True))

    def run(self):
        p = Thread(target=self._init_publisher)
        c = Thread(target=self._init_consumer)
        t = Thread(target=self._ioloop)

        print(f'Running stub "{repr(self)}" {t.getName()}')
        p.start()
        c.start()
        t.start()

        self.run_threads += [p, c, t]

    def _init_publisher(self):
        self._publisher = Publisher(self)
        self._publisher.run()

    def _init_consumer(self):
        self._consumer = Consumer(self)
        self._consumer.run()

    def _ioloop(self):
        while True:
            proto, out = self._queue.get()
            if self._pipe.args.debug:
                method = 'Sending' if out else 'Received'
                print(f'{method} proto "{proto.__class__.__name__}"...')

            if out:
                self._publisher._queue.put(proto)
            else:
                self.process(proto)

    def join(self):
        for t in self.run_threads:
            print(f'Waiting for stub "{repr(self)}" to finish {t.getName()}')
            t.join()
            self.run_threads.clear()


class Connector:
    _connection = None
    _channel = None
    _closing = False
    _url = None

    def __init__(self, _stub):
        self._stub = _stub
        conn = _stub._pipe.active_connection
        self._url = f'amqp://{conn.username}:{conn.password}@{conn.host}:{conn.port}/{self._stub._pipe}'

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.
        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.
        :rtype: pika.SelectConnection
        """
        if self._stub._pipe.args.debug:
            print(f'Connecting "{self}" stub to {self._url}')
        return pika.SelectConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed)

    def close_connection(self):
        self._consuming = False
        if self._connection.is_closing or self._connection.is_closed:
            print('Connection is closing or already closed')
        else:
            print('Closing connection')
            self._connection.close()

    def on_connection_open(self, _unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.
        :param pika.SelectConnection _unused_connection: The connection
        """
        print('Connection opened')
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        """This method is called by pika if the connection to RabbitMQ
        can't be established.
        :param pika.SelectConnection _unused_connection: The connection
        :param Exception err: The error
        """
        print(f'Connection open failed: {err}')
        self.reconnect()

    def on_connection_closed(self, _unused_connection, reason):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.
        :param pika.connection.Connection connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.
        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            print(f'Connection closed, reconnect necessary: {reason}')
            self.reconnect()

    def reconnect(self):
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.
        """
        print('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.
        Since the channel is now open, we'll declare the exchange to use.
        :param pika.channel.Channel channel: The channel object
        """
        if self._stub._pipe.args.debug:
            print('Channel opened')

        self._channel = channel
        self.add_on_channel_close_callback()

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.
        """
        if self._stub._pipe.args.debug:
            print('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.
        :param pika.channel.Channel channel: The closed channel
        :param Exception reason: why the channel was closed
        """
        print(f'Channel {channel} was closed: {reason}')
        self.close_connection()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.
        """
        print('Closing the channel')
        self._channel.close()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.
        """
        if not self._closing:
            self._closing = True
            print('Stopping')
            if self._consuming:
                self.stop_consuming()
                self._connection.ioloop.start()
            else:
                self._connection.ioloop.stop()
            print('Stopped')


class Consumer(Connector):
    _consumer_tag = None
    _consuming = False

    def set_qos(self):
        """This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one. You should experiment
        with different prefetch values to achieve desired performance.
        """
        self._channel.basic_qos(
            prefetch_count=self._stub._pipe.prefetch, callback=self.on_basic_qos_ok)

    def on_basic_qos_ok(self, _unused_frame):
        """Invoked by pika when the Basic.QoS method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.
        :param pika.frame.Method _unused_frame: The Basic.QosOk response frame
        """
        if self._stub._pipe.args.debug:
            print(f'QOS set to: {self._stub._pipe.prefetch}')

        self.start_consuming()

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.
        """
        if self._stub._pipe.args.debug:
            print('Issuing consumer related RPC commands')

        self.add_on_cancel_callback()

        queue = repr(self._stub._service) + '.' + repr(self)
        self._consumer_tag = self._channel.basic_consume(queue, self.on_message)
        self._consuming = True

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.
        """
        if self._stub._pipe.args.debug:
            print('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.
        :param pika.frame.Method method_frame: The Basic.Cancel frame
        """
        print(f'Consumer was cancelled remotely, shutting down: {method_frame}')
        if self._channel:
            self._channel.close()

    def on_message(self, channel, method, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.
        :param pika.channel.Channel channel: The channel object
        :param pika.Spec.Basic.Deliver method:
        :param pika.Spec.BasicProperties properties:
        :param bytes body: The message body
        """
        proto = self._stub._InProto()
        proto.ParseFromString(body)

        if self._stub._pipe.args.debug:
            print(f'"{self}" stub received "{proto.__class__.__name__}" message on {channel}...')

        self._stub._queue.put((proto, False))
        self.acknowledge_message(method.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.
        :param int delivery_tag: The delivery tag from the Basic.Deliver frame
        """
        if self._stub._pipe.args.debug:
            print('Acknowledging message %s', delivery_tag)
            self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.
        """
        if self._channel:
            if self._stub._pipe.args.debug:
                print('Sending a Basic.Cancel RPC command to RabbitMQ')

            cb = functools.partial(self.on_cancelok, userdata=self._consumer_tag)
            self._channel.basic_cancel(self._consumer_tag, cb)

    def on_cancelok(self, _unused_frame, userdata):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.
        :param pika.frame.Method _unused_frame: The Basic.CancelOk frame
        :param str|unicode userdata: Extra user data (consumer tag)
        """
        self._consuming = False
        if self._stub._pipe.args.debug:
            print(f'RabbitMQ acknowledged the cancellation of the consumer: {userdata}')
        self.close_channel()


class Publisher(Connector):
    _publish_interval = 1
    _deliveries = []
    _message_number = 0
    _acked = 0
    _nacked = 0
    _queue = Queue()
    _stopping = False

    def run(self):
        """Run the example code by connecting and then starting the IOLoop.
        """
        while not self._stopping:
            self._connection = None
            self._deliveries = []
            self._acked = 0
            self._nacked = 0
            self._message_number = 0

            try:
                self._connection = self.connect()
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()
                if (self._connection is not None and
                        not self._connection.is_closed):
                    # Finish closing
                    self._connection.ioloop.start()

        print('Stopped')

    def publish_message(self):
        """If the class is not stopping, publish a message to RabbitMQ,
        appending a list of deliveries with the message number that was sent.
        This list will be used to check for delivery confirmations in the
        on_delivery_confirmations method.
        Once the message has been sent, schedule another message to be sent.
        The main reason I put scheduling in was just so you can get a good idea
        of how the process is flowing by slowing down and speeding up the
        delivery intervals by changing the PUBLISH_INTERVAL constant in the
        class.
        """

        debug = self._stub._pipe.args.debug
        if debug:
            print('Publishing message...')

        if self._channel is None or not self._channel.is_open:
            print(f'"{self}" stub channel closed')
            return

        proto = self._queue.get()

        # check proto type against expected type
        proto_cls = proto.__class__.__name__

        if self._stub._OutStub._in_proto != proto_cls:
            self._stub.raise_wrong_msg_type(proto_cls)

        body = proto.SerializeToString()

        if debug:
            print(f'"{self}" stub publishing "{proto_cls}" to {self._stub._out_stub}...')

        self._channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=repr(self._stub._out_stub),
            body=body,
            properties=PROPS
        )

        self._message_number += 1
        self._deliveries.append(self._message_number)
        if debug:
            print('Published message # %i', self._message_number)

    def start_publishing(self):
        """This method will enable delivery confirmations and schedule the
        first message to be sent to RabbitMQ
        """

        print('Issuing consumer related RPC commands')
        self.enable_delivery_confirmations()
        self.schedule_next_message()

    def enable_delivery_confirmations(self):
        """Send the Confirm.Select RPC method to RabbitMQ to enable delivery
        confirmations on the channel. The only way to turn this off is to close
        the channel and create a new one.
        When the message is confirmed from RabbitMQ, the
        on_delivery_confirmation method will be invoked passing in a Basic.Ack
        or Basic.Nack method from RabbitMQ that will indicate which messages it
        is confirming or rejecting.
        """
        print('Issuing Confirm.Select RPC command')
        self._channel.confirm_delivery(self.on_delivery_confirmation)

    def on_delivery_confirmation(self, method_frame):
        """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
        command, passing in either a Basic.Ack or Basic.Nack frame with
        the delivery tag of the message that was published. The delivery tag
        is an integer counter indicating the message number that was sent
        on the channel via Basic.Publish. Here we're just doing house keeping
        to keep track of stats and remove message numbers that we expect
        a delivery confirmation of from the list used to keep track of messages
        that are pending confirmation.
        :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame
        """
        debug = self._stub._pipe.args.debug
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        if debug:
            tag = method_frame.method.delivery_tag
            print(f'Received {confirmation_type} for delivery tag: {tag}')
        if confirmation_type == 'ack':
            self._acked += 1
        elif confirmation_type == 'nack':
            self._nacked += 1
        self._deliveries.remove(method_frame.method.delivery_tag)
        if debug:
            print(f'Published {self._message_number} messages, {len(self._deliveries)}'
                  f'have yet to be confirmed {self._acked} were acked and'
                  f'{self._nacked} were nacked')

    def schedule_next_message(self):
        """If we are not closing our connection to RabbitMQ, schedule another
        message to be delivered in PUBLISH_INTERVAL seconds.
        """
        if self._stub._pipe.args.debug:
            print(f'Scheduling next message for {self._publish_interval} seconds')

        self._connection.ioloop.call_later(self._publish_interval, self.publish_message)