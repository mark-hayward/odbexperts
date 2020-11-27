import json


def base_validation(event):
	# TODO Temporary validation until SAM adds RequestValidator to template.
	if 'queryStringParameters' not in event or event['queryStringParameters'] is None:
		print("Parameters missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Parameters vin and requestType required."})
		}
	return "OK"


def request_validation(event):
	base_valid = base_validation(event)

	if base_valid != "OK":
		return base_valid

	if 'reg' not in event['queryStringParameters'] or event['queryStringParameters']['reg'] == "":
		print("Registration missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Registration missing from URL."})
		}
	if 'year' not in event['queryStringParameters'] or event['queryStringParameters']['year'] == "":
		print("Year missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Year missing from URL."})
		}

	if 'make' not in event['queryStringParameters'] or event['queryStringParameters']['make'] == "":
		print("Make missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Make missing from URL."})
		}

	if 'model' not in event['queryStringParameters'] or event['queryStringParameters']['model'] == "":
		print("Model missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Model missing from URL."})
		}

	if 'fuel' not in event['queryStringParameters'] or event['queryStringParameters']['fuel'] == "":
		print("Fuel type missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Fuel type missing from URL."})
		}

	if 'engine' not in event['queryStringParameters'] or event['queryStringParameters']['engine'] == "":
		print("Engine size missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Engine size missing from URL."})
		}

	if 'requestType' not in event['queryStringParameters'] or event['queryStringParameters']['requestType'] == "":
		print("Request type missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Request type missing from URL."})
		}

	return "OK"


def convert_validation(event):
	base_valid = base_validation(event)

	if base_valid != "OK":
		return base_valid

	if 'raw_data' not in event['queryStringParameters'] or event['queryStringParameters']['raw_data'] == "":
		print("Raw data missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Raw data missing from URL."})
		}
	if 'reg' not in event['queryStringParameters'] or event['queryStringParameters']['reg'] == "":
		print("Registration missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Registration missing from URL."})
		}
	if 'year' not in event['queryStringParameters'] or event['queryStringParameters']['year'] == "":
		print("Year missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Year missing from URL."})
		}

	if 'make' not in event['queryStringParameters'] or event['queryStringParameters']['make'] == "":
		print("Make missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Make missing from URL."})
		}

	if 'model' not in event['queryStringParameters'] or event['queryStringParameters']['model'] == "":
		print("Model missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Model missing from URL."})
		}

	if 'fuel' not in event['queryStringParameters'] or event['queryStringParameters']['fuel'] == "":
		print("Fuel type missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Fuel type missing from URL."})
		}

	if 'engine' not in event['queryStringParameters'] or event['queryStringParameters']['engine'] == "":
		print("Engine size missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Engine size missing from URL."})
		}

	if 'requestType' not in event['queryStringParameters'] or event['queryStringParameters']['requestType'] == "":
		print("Request type missing.")
		return {
			# Bad Request
			"statusCode": 400,
			"body": json.dumps({"message": "Request type missing from URL."})
		}
			
	if 'conv_units' not in event['queryStringParameters'] or event['queryStringParameters']['conv_units'] == "":
		print("Units missing")
		return {
			# Bad request
			"statusCode": 400,
			"body": json.dumps({"message": "Units missing from the URL"})
		}

	return "OK"
