import json
import logging

import pika


class RabbitMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.request_queue = 'stock_length_request_queue'
        self.response_queue = 'stock_length_response_queue'

    def connect(self):
        # Read RabbitMQ credentials from secrets file
        with open('secrets.json') as f:
            secrets = json.load(f)

        rabbitmq_host = secrets['rabbitmq_host']
        rabbitmq_port = secrets['rabbitmq_port']
        rabbitmq_username = secrets['rabbitmq_username']
        rabbitmq_password = secrets['rabbitmq_password']

        credentials = pika.PlainCredentials(rabbitmq_username, rabbitmq_password)
        parameters = pika.ConnectionParameters(host=rabbitmq_host,
                                               port=rabbitmq_port,
                                               virtual_host='/',
                                               credentials=credentials)

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        self.setup_queues()


    def setup_queues(self):
        self.channel.queue_declare(queue=self.request_queue)
        self.channel.queue_declare(queue=self.response_queue)


    def start_consuming(self, callback):
        self.channel.basic_consume(queue=self.request_queue, on_message_callback=callback, auto_ack=True)
        print(' [*] Waiting for messages. To exit, press CTRL+C')
        self.channel.start_consuming()

    def send_reply(self, message):
        # Log the outgoing message
        logging.info(f"Sent: {message}")
        self.channel.basic_publish(exchange='', routing_key=self.response_queue, body=message)

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
