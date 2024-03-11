# LengthNestProMQ
LengthNestProMQ is a free software application for one-dimensional nest optimization. It minimizes scrap when cutting raw material lengths into shorter pieces or parts.

It is an adaption of LengthNestPro from which the GUI is removed and RabbitMQ is integrated.   

To use the software:
  1. Create a copy of the secrets.default.json file in the config directory.
  2. Change the values of the entries in the secrets.json file. 
  3. Run main.py
  4. Add a message to a queue called: `stock_length_request_queue`
  5. Get the response from the queue: `stock_length_response_queue`
  6. Optionally view logs in logs directory
