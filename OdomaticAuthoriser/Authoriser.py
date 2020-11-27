import base64
import hashlib
import uuid

import boto3
from boto3.dynamodb.conditions import Key, Attr


def create_policy(method_arn, allow):
	tmp = method_arn.split(":")
	apiGatewayTmp = tmp[5].split("/")
	policy = {
		"principalId": f"{str(uuid.uuid1())}",
		"policyDocument": {
			"Version": "2012-10-17",
			"Statement": [
				{
					"Effect": "Allow" if allow else "Deny",
					"Action": [
						"execute-api:Invoke"
					],
					"Resource": [
						f"arn:aws:execute-api:{tmp[3]}:{tmp[4]}:{apiGatewayTmp[0]}/{apiGatewayTmp[1]}/GET/*"
					]
				}
			]
		}
	}

	return policy


def handler(event, context):
	print(event)
	dbClient = boto3.resource('dynamodb')
	cred_table = dbClient.Table('Credentials')

	token = event['authorizationToken']
	methodArn = event['methodArn']

	# TestUser396:W1th0utS3rv3rs593^*
	user = base64.decodebytes(token.encode('utf-8')).decode('utf-8').split(':')[0]
	pwdMD5 = hashlib.md5(base64.decodebytes(token.encode('utf-8')).decode('utf-8').split(':')[1].encode('utf-8'))

	response = cred_table.query(
		KeyConditionExpression=Key('UserId').eq(user),
		FilterExpression=Attr('PwdHash').eq(pwdMD5.hexdigest())
	)

	# If we found the user we can proceed
	if response['Items']:
		return create_policy(methodArn, True)
	else:
		return create_policy(methodArn, False)
