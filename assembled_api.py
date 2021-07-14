import os
import requests
import collections
import ciso8601 as ciso
import time
import json
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Assembled:
    def __init__(self):
        self.base_url = 'https://api.assembledhq.com/v0'
        self.credentials = (os.environ['ASSEMBLED_TOKEN'], '')
        self.headers = {'Content-Type': 'application/json'}

    def get_activities(self):
        url = f'{self.base_url}/activity_types'
        response = requests.get(url, auth=self.credentials)
        return response.text

    def _get_agent_id(self, slack_email):
        url = f'{self.base_url}/agents'
        response = requests.get(url, auth=self.credentials)
        data = json.loads(response.text)
        agents = data['agents']

        for agent in agents.values():
            email = agent.get('email')
            if email == slack_email:
                assembled_id = agent.get('id')

        return assembled_id

    def _convert_dates(self, start_date, start_date_period, end_date, end_date_period):
        start_add = ''
        end_add = ''

        if start_date_period == 'all_day':
            start_add = 'T00:00:00+00:00'
        elif start_date_period == 'morning':
            start_add = 'T08:00:00+00:00'
        elif start_date_period == 'afternoon':
            start_add = 'T12:00:00+00:00'

        if end_date_period == 'all_day':
            end_add = 'T17:00:00+00:00'
        elif end_date_period == 'morning':
            end_add = 'T12:00:00+00:00'
        elif end_date_period == 'afternoon':
            end_add = 'T24:00:00+00:00'

        iso_start_time = start_date + start_add
        iso_end_time = end_date + end_add

        raw_start_time = ciso.parse_datetime(iso_start_time)
        raw_end_time = ciso.parse_datetime(iso_end_time)
        unix_start_time = int(time.mktime(raw_start_time.timetuple()))
        unix_end_time = int(time.mktime(raw_end_time.timetuple()))

        return (unix_start_time, unix_end_time)

    def submit_timeoff_request(self, email, policy_type, start_date, start_date_period, end_date, end_date_period, description):
        url = f'{self.base_url}/activities'

        times = self._convert_dates(start_date=start_date, start_date_period=start_date_period, end_date=end_date, end_date_period=end_date_period)
        start_time = times[0]
        end_time = times[1]
        agent_id = self._get_agent_id(email)

        if policy_type == 'Holiday':
            type_id = '8f32ae29-66ac-4a39-8541-fa2b6f2d9983'
        elif policy_type == 'Sickness':
            type_id = "b5590baf-fdd0-41f8-900f-f2bd06fc0370"

        data = {"start_time": start_time,
                "end_time": end_time,
                "agent_id": agent_id,
                "type_id": type_id}

        response = requests.post(url, headers=self.headers, auth=self.credentials, data=json.dumps(data))
        return response.status_code
