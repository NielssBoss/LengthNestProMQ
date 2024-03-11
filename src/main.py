import json
import logging

import numpy as np

from rabbitmq_manager import RabbitMQManager
from nest_calculation_new import CalculateObject


def extract_data_from_json_formatted_string(json_formatted_string):
    # Load JSON data from file
    try:
        data = json.loads(json_formatted_string)
    except json.JSONDecodeError as e:
        rabbit_manager.send_reply("Error decoding JSON:" + str(e))
        return None

    # Extract required parts data
    required_parts = data["required_parts"]

    # Extract lengths, quantities, and names of required parts
    parts_lengths = np.array([part["length"] for part in required_parts])
    parts_quant = np.array([part["quantity"] for part in required_parts])
    parts_names = np.array([part["name"] for part in required_parts])

    # Extract stock data
    stock = data["stock"]

    # Return extracted data
    return (parts_lengths, parts_quant, parts_names,
            stock["length"], stock["waste_left"], stock["waste_right"],
            stock["spacing"], stock["max_parts_per_nest"], stock["max_containers"])


def start_calculation(ch, method, properties, body):

    logging.info(f"Received: {body}")
    extracted_data = extract_data_from_json_formatted_string(body)

    if extracted_data is None:
        return

    (part_lengths, part_quantities, part_names,
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

    rabbit_manager.send_reply(json.dumps(parts_distribution))


# Configure logging
logging.basicConfig(filename='../logs/rabbitmq_logs.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

rabbit_manager = RabbitMQManager()

rabbit_manager.connect()

# Start consuming messages
rabbit_manager.start_consuming(start_calculation)
