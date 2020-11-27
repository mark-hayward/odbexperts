import base64
import ctypes.util
import json
import os
from datetime import datetime
from time import time

import boto3
from Validation import request_validation, convert_validation
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


def get_version(lib, event):
	# check version of odomatic (returns number)
	version = lib.Odomatic_GetVersion()
	print("Loaded Odomatic Version", version)
	return {
		"statusCode": 200,
		"body": json.dumps({"version": version})
	}


def get_request(lib, event, path):
	# Validation for this method.
	validation = request_validation(event)
	if validation != 'OK':
		return validation

	make = int(event['queryStringParameters']['make'])
	model = int(event['queryStringParameters']['model'])
	year = int(event['queryStringParameters']['year'])
	fuel = int(event['queryStringParameters']['fuel'])
	engine = int(event['queryStringParameters']['engine'])
	request_num = int(event['queryStringParameters']['requestType'])
	reg = event['queryStringParameters']['reg'].replace(" ", "").upper()

	if "ReportPID" == path:
		emailClient = boto3.client('ses', region_name='eu-west-1')
		CHARSET = 'UTF-8'

		nl = '\n'
		BODY_TEXT = f"""
			Reg: {reg}{nl}
			Model: {model}{nl}
			Make: {make}{nl}
			Engine: {engine}{nl}
			Fuel: {fuel}{nl}
			Year: {year}{nl}
			Request Type: {request_num}
			"""

		BODY_HTML = f"""<html>
			<head><head>
			<body>
				<ul>
					<li>Reg: {reg}</li>
					<li>Model: {model}</li>
					<li>Make: {make}</li>
					<li>Engine: {engine}</li>
					<li>Fuel: {fuel}</li>
					<li>Year: {year}</li>
					<li>Request Type: {request_num}</li>
				</ul>
			</body>
			</html>
			"""

		# Try to send the email.
		try:
			# Provide the contents of the email.
			response = emailClient.send_email(
				Destination={
					'ToAddresses': [
						'beth@obdexperts.co.uk',
					],
				},
				Message={
					'Body': {
						'Html': {
							'Charset': CHARSET,
							'Data': BODY_HTML,
						},
						'Text': {
							'Charset': CHARSET,
							'Data': BODY_TEXT,
						},
					},
					'Subject': {
						'Charset': CHARSET,
						'Data': "Report PID",
					},
				},
				Source="support@obdexperts.co.uk"
			)
		# Display an error if something goes wrong.
		except ClientError as e:
			print(e.response['Error']['Message'])
		else:
			print("Email sent! Message ID:"),
			print(response['MessageId'])

		# Provided all validation checks out. Send the email.
		return {
			"statusCode": 200,
			"body": json.dumps({"message": "Thank you for the report."})
		}
	else:
		path_libc = ctypes.util.find_library("c")
		try:
			libc = ctypes.CDLL(path_libc)
		except OSError as error:
			print(error)
			print("Cannot load c lib")
			return {
				"statusCode": 500,
				"body": json.dumps({"message": f"Cannot load c lib.\nError: {error}"})
			}

		c_make = ctypes.c_ubyte(make)
		c_model = ctypes.c_ubyte(model)
		c_year = ctypes.c_ushort(year)
		c_fuel = ctypes.c_ubyte(fuel)
		c_engine = ctypes.c_ubyte(engine)
		c_request_num = ctypes.c_ubyte(request_num)
		resp_str = ctypes.create_string_buffer(16)
		libc.memset(resp_str, ctypes.c_char(b"X"), 15)

		# reg must be alphanumeric
		if not reg.isalnum():
			print("Unsupported reg - not alphanumeric")
			return {
				"statusCode": 400,
				"body": json.dumps({"message": "Unsupported registration - not alphanumeric"})
			}
		else:
			if lib.Odomatic_GetRequestByMMYFESecure(c_make, c_model, c_year, c_fuel, c_engine, c_request_num,
											 ctypes.byref(resp_str)) == 0:
				print("Successfully retrieved info for reg ", reg)
				print("Resp buffer now contains ")
				result = []
				for x in range(0, 15):
					print(" -", resp_str[x])
					result.append(ord(resp_str[x]))

				# Update Dynamo
				update_dynamo(token=event['headers']['Authorization'],
							  request_type="GetRequest",
							  reg=reg,
							  year=year,
							  make=make,
							  model=model,
							  engine=engine,
							  fuel=fuel,
							  request_num=request_num,
							  raw_data=None)
				return {
					"statusCode": 200,
					"body": json.dumps({"result": result})
				}
			else:
				# Update Dynamo
				update_dynamo(token=event['headers']['Authorization'],
							  request_type="GetRequest",
							  reg=reg,
							  year=year,
							  make=make,
							  model=model,
							  engine=engine,
							  fuel=fuel,
							  request_num=request_num,
							  raw_data=None)
				print("Unsupported request for", reg)
				return {
					"statusCode": 200,
					"body": json.dumps({"message": f"Unsupported request  {reg}"})
				}


def convert(lib, event):
	validation = convert_validation(event)

	if validation != "OK":
		return validation
	make = int(event['queryStringParameters']['make'])
	model = int(event['queryStringParameters']['model'])
	year = int(event['queryStringParameters']['year'])
	fuel = int(event['queryStringParameters']['fuel'])
	engine = int(event['queryStringParameters']['engine'])
	request_num = int(event['queryStringParameters']['requestType'])
	conv_units = int(event['queryStringParameters']['conv_units'])
	c_make = ctypes.c_ubyte(make)
	c_model = ctypes.c_ubyte(model)
	c_year = ctypes.c_ushort(year)		
	c_fuel = ctypes.c_ubyte(fuel)
	c_engine = ctypes.c_ubyte(engine)
	c_request_num = ctypes.c_ubyte(request_num)
	c_conv_units = ctypes.c_ubyte(conv_units)
	reg = event['queryStringParameters']['reg'].replace(" ", "").upper()
	
	raw_data = str(event['queryStringParameters']['raw_data'])
	raw_data_str = bytes.fromhex(raw_data)
	raw_data_hex = ctypes.create_string_buffer(raw_data_str)
	pi = ctypes.pointer(raw_data_hex)

	conv_result = ctypes.c_ulong(0)
	conv_fraction = ctypes.c_ulong(0)
	
	if lib.Odomatic_ConvertByMMYFE(c_make, c_model, c_year, c_fuel, c_engine, c_request_num, pi, c_conv_units, ctypes.byref(conv_result), ctypes.byref(conv_fraction)) == 0:
		print("Successfully retrieved conversion")
		result = ("%d.%d" % (conv_result.value, conv_fraction.value))
		#result = ("%s %s %s" % (raw_data, ctypes.string_at(raw_data_hex,len(raw_data_str)), raw_data_str.hex()))
		#result = "read params"
	else:
		#result = ("%s" % raw_data_hex.value)
		#result = ("%s %s %s" % (raw_data, ctypes.string_at(raw_data_hex,len(raw_data_str)), raw_data_str.hex()))
		#result = ("%d %d" % (len1,len3))
		result = "unsupported conversion"

	# Update Dynamo
	update_dynamo(token=event['headers']['Authorization'],
					 request_type="Convert",
					 reg=reg,
					 year=year,
					 make=make,
					 model=model,
					 engine=engine,
					 fuel=fuel,
					 request_num=request_num,
					 raw_data=raw_data)
	return {
		"statusCode": 200,
		"body": json.dumps({"result": result})
	}


def update_dynamo(token, request_type, reg, year, make, model, engine, fuel, request_num, raw_data):
	user = base64.decodebytes(token.encode('utf-8')).decode('utf-8').split(':')[0]
	date = datetime.now().strftime('%Y-%m')
	table = boto3.resource('dynamodb').Table('OBDRequests')
	# Insert the request into the DB.
	table.put_item(
		Item={
			"UserId": user,
			"Timestamp": int(time()),
			"Date": date,
			"RequestType": request_type,
			"Reg": reg,
			"Year": year if year else ' ',
			"Make": make if make else ' ',
			"Model": model if model else ' ',
			"Engine": engine if engine else ' ',
			"Fuel": fuel if fuel else ' ',
			"ReqNum": request_num if request_num else ' ',
			"RawData": raw_data if raw_data else ' '
		}
	)


def handler(event, context):
	print(event)
	try:
		TestLib = ctypes.CDLL(os.path.abspath('libOdomatic.so'))
	except OSError as error:
		print(error)
		print("Cannot load Odomatic lib")
		return {
			"statusCode": 500,
			"body": json.dumps({"message": f"Cannot load Odomatic lib.\nError: {error}"})
		}

	# Depending on path determines outcome
	path = event['path'].strip('/')

	# GetVersion
	if "GetVersion" == path:
		return get_version(TestLib, event)

	# Convert
	elif "Convert" == path:
		return convert(TestLib, event)

	# GetRequest or ReportPID
	return get_request(TestLib, event, path)
