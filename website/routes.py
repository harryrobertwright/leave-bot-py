import slack
import os
import os.path
import json
import datetime
from bob import Bob
from assembled_api import Assembled
from pathlib import Path
import uuid
from dotenv import load_dotenv
from flask import Blueprint, request, Response

routes = Blueprint('routes', __name__)

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
bob = Bob()
assembled = Assembled()

with open('website/blocks/modal.json') as file:
  modal = json.load(file)

@routes.route('/bot', methods=['POST'])
def bot():
    response_data = request.form.to_dict()
    raw_payload = response_data.get('payload')
    payload = json.loads(raw_payload)
    payload_type = payload.get('type')
    trigger_id = payload.get('trigger_id')
    request_user = payload.get('user')
    slack_id = request_user.get('id')
    user_info = client.users_info(user=slack_id)
    user = user_info.get('user')
    profile = user.get('profile')
    name = profile.get('real_name')
    email = profile.get('email')
    boss = bob.get_reports_to_email(email)

    with open("payload.json", "w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    if payload_type == 'shortcut':
        client.views_open(trigger_id=trigger_id, view=modal)
    elif payload_type == 'view_submission':
        handleNewRequest(payload)
    elif payload_type == 'block_actions':
        request_id = getRequestId(payload)

        updateRequests(request_id, payload)

        request_info = getRequest(request_id)

        employee_id = bob.get_employee_id(request_info['user'])
        email = request_info['user']
        policy_type = request_info['policyType']
        start_date = request_info['startDate']
        start_date_period = request_info['startDatePortion']
        end_date = request_info['endDate']
        end_date_period = request_info['endDatePortion']
        description = request_info['description']
        skip_manager_approval = True
        approver = bob.get_reports_to_id(request_info['approver'])
        approver_slack_id = getSlackID(request_info['approver'])

        request_responses = submitRequests(email=email, employee_id=employee_id, policy_type=policy_type, start_date=start_date, start_date_period=start_date_period, end_date=end_date, end_date_period=end_date_period, description=description, skip_manager_approval=skip_manager_approval, approver=approver)
        if request_responses[0] == 200:
            client.chat_postMessage(channel='#leave-bot-test', text='Leave successfully booked with Bob!')
        else:
            client.chat_postMessage(channel='#leave-bot-test', text='Holiday booking unsuccessful with Bob!')

        if request_responses[1] == 200:
            client.chat_postMessage(channel='#leave-bot-test', text='Leave successfully booked with Assembled!')
        else:
            client.chat_postMessage(channel='#leave-bot-test', text='Holiday booking unsuccessful with Assembled!')
    else:
        pass

    return Response(), 200

def handleNewRequest(payload):
    request_id = uuid.uuid1().hex
    modal_response = payload['view']['state']['values']
    request_user = payload.get('user')
    slack_id = request_user.get('id')
    user_info = client.users_info(user=slack_id)
    user = user_info.get('user')
    profile = user.get('profile')
    name = profile.get('real_name')
    email = profile.get('email')
    boss = bob.get_reports_to_email(email)

    request_info = {}

    if os.path.isfile("requests.json") == True:
        with open("requests.json", "r") as f:
            requests_log = json.load(f)
    else:
        requests_log = {}

    for field in modal_response.values():
        for key in field.keys():
            if key == 'policyType':
                value = field[key]['selected_option']['value']
                request_info[key] = value
            elif key == 'startDate':
                value = field[key]['selected_date']
                request_info[key] = value
            elif key == 'startDatePortion':
                value = field[key]['selected_option']['value']
                request_info[key] = value
            elif key == 'endDate':
                value = field[key]['selected_date']
                request_info[key] = value
            elif key == 'endDatePortion':
                value = field[key]['selected_option']['value']
                request_info[key] = value
            elif key == 'description':
                value = field[key]['value']
                request_info[key] = value

    request_info['user'] = email
    request_info['approver'] = boss
    request_info['status'] = 'Pending'
    requests_log[request_id] = request_info

    with open("requests.json", "w") as f:
        json.dump(requests_log, f, ensure_ascii=False, indent=4)

    message = convertToMessage(request_id, request_info)

    client.chat_postMessage(channel = getSlackID(boss), text = 'New request received!', blocks = message)

def submitRequests(email, employee_id, policy_type, start_date, start_date_period, end_date, end_date_period, description, skip_manager_approval, approver):
    bob_request = bob.submit_timeoff_request(employee_id=employee_id, policy_type=policy_type, start_date=start_date, start_date_period=start_date_period, end_date=end_date, end_date_period=end_date_period, description=description, skip_manager_approval=skip_manager_approval, approver=approver)
    assembled_request = assembled.submit_timeoff_request(email=email, policy_type=policy_type, start_date=start_date, start_date_period=start_date_period, end_date=end_date, end_date_period=end_date_period, description=description)

    return (bob_request, assembled_request)

def angliciseDate(date):
    split_date = date.split('-')
    reversed_date = reversed(split_date)
    anglicised_date = '-'.join(reversed_date)

    return anglicised_date

def convertToMessage(request_id, request_info):
    start_date = angliciseDate(request_info['startDate'])
    end_date = angliciseDate(request_info['endDate'])

    start_date_period = request_info['startDatePortion'].title().replace('_', ' ')
    end_date_period = request_info['endDatePortion'].title().replace('_', ' ')

    message = [
            	{
            		"type": "section",
            		"text": {
            			"type": "mrkdwn",
            			"text": f"You have a new leave request:\n*{request_info['user']} - New {request_info['policyType']} request*"
            		}
            	},
            	{
            		"type": "section",
            		"fields": [
            			{
            				"type": "mrkdwn",
            				"text": f"*From:*\n{start_date}\n"
            			},
            			{
            				"type": "mrkdwn",
            				"text": f"*Period:*\n{start_date_period}"
            			},
            			{
            				"type": "mrkdwn",
            				"text": f"*To:*\n{end_date}"
            			},
            			{
            				"type": "mrkdwn",
            				"text": f"*Period:*\n{end_date_period}"
            			},
            			{
            				"type": "mrkdwn",
            				"text": f"*Description:*\n{request_info['description']}"
            			}
            		]
            	},
        		{
        			"type": "context",
        			"elements": [
        				{
        					"type": "plain_text",
        					"text": f'{request_id}',
        					"emoji": True
        				}
        			]
        		},
            	{
            		"type": "actions",
            		"elements": [
            			{
            				"type": "button",
            				"text": {
            					"type": "plain_text",
            					"emoji": True,
            					"text": "Approve"
            				},
            				"style": "primary",
            				"value": "approve"
            			},
            			{
            				"type": "button",
            				"text": {
            					"type": "plain_text",
            					"emoji": True,
            					"text": "Deny"
            				},
            				"style": "danger",
            				"value": "deny"
            			}
            		]
            	}
            ]
    return message

def getRequestId(payload):
    message = payload.get('message')
    blocks = message.get('blocks')

    for block in blocks:
        block_type = block.get('type')
        if block_type == 'context':
            for element in block.get('elements'):
                request_id = element.get('text')

    return request_id

def getRequest(request_id):
    with open("requests.json", "r") as f:
        requests_log = json.load(f)

    request_info = requests_log[request_id]

    return request_info

def updateRequests(request_id, payload):
    status = payload['actions'][0]['value']

    with open("requests.json", "r") as f:
        requests_log = json.load(f)

    if status == 'approve':
        requests_log[request_id]["status"] = 'Approved'
    else:
        requests_log[request_id]["status"] = 'Declined'

    with open("requests.json", "w") as f:
        json.dump(requests_log, f, ensure_ascii=False, indent=4)

def getSlackID(email):
    response = client.users_lookupByEmail(email=email)
    data = response.data
    user = data.get('user')
    id = user.get('id')
    return id
