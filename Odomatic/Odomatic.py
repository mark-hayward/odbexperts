import base64
import ctypes.util
import json
import os
from datetime import datetime
from time import time

import boto3
from Validation import request_validation, convert_validation


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

    vin = event['queryStringParameters']['vin']
    request_num = int(event['queryStringParameters']['requestType'])
    reg = event['queryStringParameters']['reg'].replace(" ", "").upper()

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

    c_vin = ctypes.c_ubyte(vin)
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
        if lib.Odomatic_GetRequestByVinSecure(c_vin, c_request_num, ctypes.byref(resp_str)) == 0:
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
                          vin=vin,
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
                          vin=vin,
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
    vin = int(event['queryStringParameters']['vin'])
    request_num = int(event['queryStringParameters']['requestType'])
    conv_units = int(event['queryStringParameters']['conv_units'])
    c_vin = ctypes.c_ubyte(vin)
    c_request_num = ctypes.c_ubyte(request_num)
    c_conv_units = ctypes.c_ubyte(conv_units)
    reg = event['queryStringParameters']['reg'].replace(" ", "").upper()

    raw_data = str(event['queryStringParameters']['raw_data'])
    raw_data_str = bytes.fromhex(raw_data)
    raw_data_hex = ctypes.create_string_buffer(raw_data_str)
    pi = ctypes.pointer(raw_data_hex)

    conv_result = ctypes.c_ulong(0)
    conv_fraction = ctypes.c_ulong(0)

    if lib.Odomatic_ConvertByVin(c_vin, c_request_num, pi, c_conv_units, ctypes.byref(conv_result),
                                 ctypes.byref(conv_fraction)) == 0:
        print("Successfully retrieved conversion")
        result = ("%d.%d" % (conv_result.value, conv_fraction.value))
    # result = ("%s %s %s" % (raw_data, ctypes.string_at(raw_data_hex,len(raw_data_str)), raw_data_str.hex()))
    # result = "read params"
    else:
        # result = ("%s" % raw_data_hex.value)
        # result = ("%s %s %s" % (raw_data, ctypes.string_at(raw_data_hex,len(raw_data_str)), raw_data_str.hex()))
        # result = ("%d %d" % (len1,len3))
        result = "unsupported conversion"

    # Update Dynamo
    update_dynamo(token=event['headers']['Authorization'],
                  request_type="Convert",
                  vin=vin,
                  reg=reg,
                  request_num=request_num,
                  raw_data=raw_data)
    return {
        "statusCode": 200,
        "body": json.dumps({"result": result})
    }


def update_dynamo(token, request_type, vin, reg, request_num, raw_data):
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
            "Vin": vin if vin else ' ',
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
