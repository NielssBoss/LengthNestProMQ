import json
import logging

import numpy as np

from LengthNestProMQ.src.day_based_rot_file_handler import DayBasedRotatingFileHandler
from rabbitmq_manager import RabbitMQManager
from nest_calculation_new import CalculateObject


def is_valid_format(data):
    # Check if the dictionary has all required keys
    required_keys = ["required_parts", "stock"]
    if not all(key in data for key in required_keys):
        return False, "'required_parts' or 'stock' missing"

    # Check the format of "required_parts"
    required_parts = data.get("required_parts")
    if not isinstance(required_parts, list):
        return False, "'required_parts' must be a list"

    for i, part in enumerate(required_parts):
        if not isinstance(part, dict) or \
                not all(key in part for key in ["name", "length", "quantity"]) or \
                not isinstance(part["name"], str) or \
                not isinstance(part["length"], (int, float)) or \
                not isinstance(part["quantity"], int):
            return False, f"Missing attributes in part number {i+1}, part: {part}"

    # Check the format of "stock"
    stock = data.get("stock")
    if not isinstance(stock, dict) or \
            not all(key in stock for key in
                    ["length", "waste_left", "waste_right", "spacing", "max_parts_per_nest", "max_containers"]) or \
            not isinstance(stock["length"], (int, float)) or \
            not isinstance(stock["waste_left"], (int, float)) or \
            not isinstance(stock["waste_right"], (int, float)) or \
            not isinstance(stock["spacing"], (int, float)) or \
            not isinstance(stock["max_parts_per_nest"], int) or \
            not isinstance(stock["max_containers"], int):
        return False, "Missing attributes in 'stock'"

    return True, None



def extract_data_from_json_formatted_string(json_formatted_string):
    # Load JSON data from file
    try:
        data = json.loads(json_formatted_string)
    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON:" + str(e))
        rabbit_manager.send_reply("Error decoding JSON:" + str(e))
        return None
    if type(data) is not dict:
        logger.error(f"Error wrong input provided, expects JSON but got {type(data)} instead")
        rabbit_manager.send_reply(f"Error wrong input provided, expects JSON but got {type(data)} instead")
        return None

    is_valid_format_, error_message = is_valid_format(data)

    if not is_valid_format_:
        response_string = f"""
            Error wrong input provided.
            {error_message}.
            expects JSON in form:
            {{
              "required_parts": [
                {{
                  "name": "string",
                  "length": number,
                  "quantity": integer
                }},
                {{
                  "name": "string",
                  "length": number,
                  "quantity": integer
                }},
                ...
              ],
              "stock": {{
                "length": number,
                "waste_left": integer,
                "waste_right": integer,
                "spacing": number,
                "max_parts_per_nest": integer,
                "max_containers": integer
              }}
            }}
            but instead got: {data} 
        """
        logger.error(response_string)
        rabbit_manager.send_reply(response_string)
        return None

    # Extract id
    request_id = data["request_id"]
    # Extract required parts data
    required_parts = data["required_parts"]

    # Extract lengths, quantities, and names of required parts
    parts_lengths = np.array([part["length"] for part in required_parts])
    parts_quant = np.array([part["quantity"] for part in required_parts])
    parts_names = np.array([part["name"] for part in required_parts])

    # Extract stock data
    stock = data["stock"]

    # Return extracted data
    return (request_id, parts_lengths, parts_quant, parts_names,
            stock["length"], stock["waste_left"], stock["waste_right"],
            stock["spacing"], stock["max_parts_per_nest"], stock["max_containers"])


def start_calculation(ch, method, properties, body):
    logger.info(f"Received: {body}")
    extracted_data = extract_data_from_json_formatted_string(body)

    if extracted_data is None:
        return

    (request_id, part_lengths, part_quantities, part_names,
     stock_length, left_waste, right_waste,
     spacing, max_parts_per_nest, max_containers
     ) = extracted_data

    part_lengths = np.transpose([part_lengths])
    part_quantities = np.transpose([part_quantities])

    calculator = CalculateObject(
        {
            "part_quantities": part_quantities,
            "part_lengths": part_lengths,
            "part_names": part_names,
            "max_containers": max_containers,
            "max_parts_per_nest": max_parts_per_nest,
            "stock_length": stock_length,
            "left_waste": left_waste,
            "right_waste": right_waste,
            "spacing": spacing,
            "error": 0,
            "current_sequence": 0
        }
    )
    final_patterns, final_allocations, part_names, lengths = calculator.length_nest_pro_calculate()
    parts_distribution = []

    for i in range(len(final_allocations)):
        parts_distribution.append(
            {"parts": [], "quantity": int(final_allocations[i]), "spacing": spacing, "stock_length": stock_length})

    for i, part in enumerate(final_patterns):
        for j, part_quantity in enumerate(part):
            if part_quantity > 0:
                parts_distribution[j]["parts"].append(
                    {"name": part_names[i], "length": float(lengths[i]), "quantity": part_quantity})

    rabbit_manager.send_reply(json.dumps({"request_id": request_id, "parts_distribution": parts_distribution}))


# Create logger
logger = logging.getLogger("DayBasedLogger")
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create handler
handler = DayBasedRotatingFileHandler(filename='../logs/log_{date}.log', backup_count=60)
handler.setFormatter(formatter)
logger.addHandler(handler)


rabbit_manager = RabbitMQManager()

rabbit_manager.connect()

# Start consuming messages
rabbit_manager.start_consuming(start_calculation)
