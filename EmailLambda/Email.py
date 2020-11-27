import csv
import os
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import groupby

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta
from EmailLambda.tabulate import tabulate


def handler(event, context):
	# Needed as f strings do not allow backslashes.
	nl = "\n"
	month = (datetime.now() - relativedelta(months=1)).strftime('%B %Y')
	table = boto3.resource('dynamodb').Table('OBDRequests')
	response = table.query(
		IndexName='Date-Index',
		KeyConditionExpression=Key('Date').eq((datetime.now() - relativedelta(months=1)).strftime('%Y-%m')),
	)

	if response['Items']:
		# Create CSV
		with open("/tmp/requests.csv", 'w') as csv_file:
			writer = csv.DictWriter(csv_file, response['Items'][0].keys())
			writer.writeheader()
			writer.writerows([row for row in response['Items']])

		# Group all requests this month by UserId and count how many GetRequests have been made.
		group_requests = [{
			"UserId": key,
			# Group by reg to get the number of unique registrations queried and then only count the GetRequests
			"Requests": len(set([y['Reg'] for y in list(value) if y['RequestType'] == 'GetRequest']))
		} for key, value in groupby(response['Items'], key=lambda x: x['UserId'])]

		# Replace sender@example.com with your "From" address.
		# This address must be verified with Amazon SES.
		SENDER = "Odomatic Requests <mhayward@withoutservers.com>"

		# Replace recipient@example.com with a "To" address. If your account
		# is still in the sandbox, this address must be verified.
		RECIPIENT = "beth@obdexperts.co.uk"

		# The subject line for the email.
		SUBJECT = f"Requests for {month}"

		# The full path to the file that will be attached to the email.
		ATTACHMENT = "/tmp/requests.csv"

		# The character encoding for the email.
		CHARSET = "UTF-8"

		data = [[x['UserId'], x['Requests']] for x in group_requests]

		# The email body for recipients with non-HTML email clients.
		BODY_TEXT = f"Requests made for {month}{nl}{nl.join([f'{x[0]} : {x[1]}' for x in data])}"

		# The HTML body of the email.
		BODY_HTML = f"""<html>
		<head></head>
		<body>
			<h1>Requests made for {month}</h1>
			{tabulate(data, headers=['UserId', 'Unique Requests'], tablefmt="html")}
		</body>
		</html>
		"""

		# Create a new SES resource.
		client = boto3.client('ses', region_name='eu-west-1')

		# Create a multipart/mixed parent container.
		msg = MIMEMultipart('mixed')
		# Add subject, from and to lines.
		msg['Subject'] = SUBJECT
		msg['From'] = SENDER
		msg['To'] = RECIPIENT

		# Create a multipart/alternative child container.
		msg_body = MIMEMultipart('alternative')

		# Encode the text and HTML content and set the character encoding. This step is
		# necessary if you're sending a message with characters outside the ASCII range.
		textpart = MIMEText(BODY_TEXT, 'plain', CHARSET)
		htmlpart = MIMEText(BODY_HTML, 'html', CHARSET)

		# Add the text and HTML parts to the child container.
		msg_body.attach(textpart)
		msg_body.attach(htmlpart)

		# Define the attachment part and encode it using MIMEApplication.
		att = MIMEApplication(open(ATTACHMENT, 'rb').read())

		# Add a header to tell the email client to treat this part as an attachment,
		# and to give the attachment a name.
		att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ATTACHMENT))

		# Attach the multipart/alternative child container to the multipart/mixed
		# parent container.
		msg.attach(msg_body)

		# Add the attachment to the parent container.
		msg.attach(att)

		# Try to send the email.
		try:
			# Provide the contents of the email.
			response = client.send_raw_email(
				Source=SENDER,
				Destinations=[
					RECIPIENT
				],
				RawMessage={
					'Data': msg.as_string()
				}
			)
		# Display an error if something goes wrong.
		except ClientError as e:
			print(e.response['Error']['Message'])
		else:
			print("Email sent! Message ID:"),
			print(response['MessageId'])
	else:
		print("No data found")
