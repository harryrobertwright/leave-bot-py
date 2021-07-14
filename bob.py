import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

class Bob:
    '''A class to wrap Bob's API'''
    def __init__(self):
        '''Constructs all the necessary attributes for the Bob object'''
        self.timeoff_headers = {"Authorization": os.environ['BOB_TIMEOFF_TOKEN']}
        self.base_url = 'https://api.hibob.com/v1'
        self.employee_headers = {"Authorization": os.environ['BOB_EMPLOYEE_TOKEN']}

    def submit_timeoff_request(self, employee_id, policy_type, start_date, start_date_period, end_date, end_date_period, skip_manager_approval, approver, description):
        '''Takes timeoff request information, submits to API'''
        url = f'{self.base_url}/timeoff/employees/{employee_id}/requests'

        payload = {
            "policyType": policy_type,
            "startDate": start_date,
            "startDatePortion": start_date_period,
            "endDate": end_date,
            "endDatePortion": end_date_period,
            "skipManagerApproval": skip_manager_approval,
            "approver": approver,
            "description": description
        }

        self.timeoff_headers.update({"Content-Type": "application/json"})
        response = requests.request("POST", url, json=payload, headers=self.timeoff_headers)
        return response.status_code

    def cancel_timeoff_request(self, employee_id, request_id):
        '''Takes timeoff request ID, sends delete request on Bob's API'''
        url = f'{self.base_url}/timeoff/employees/{employee_id}/requests/{request_id}'
        response = requests.request("DELETE", url, headers=self.timeoff_headers)

    def get_timeoff_request(self, employee_id, request_id):
        '''Takes timeoff request ID, returns timeoff request details'''
        url = f'https://api.hibob.com/v1/timeoff/employees/{employee_id}/requests/{request_id}'
        self.timeoff_headers.update({"Accept": "application/json"})
        response = requests.request("GET", url, headers=self.timeoff_headers)
        return response.text

    def get_employee(self, identifier):
        '''Takes employee email/ID, returns employee's profile details'''
        url = f'{self.base_url}/people/{identifier}'
        self.employee_headers.update({"Accept": "application/json"})
        response = requests.request("GET", url, headers=self.employee_headers)
        return response.text

    def get_employee_id(self, email):
        '''Takes employee email, returns employee's ID'''
        info = self.get_employee(email)
        dict = json.loads(info)
        return dict['id']

    def get_reports_to_email(self, employee_id):
        '''Takes employee ID, returns the email address who the employee reports to'''
        info = self.get_employee(employee_id)
        dict = json.loads(info)
        return dict['work']['reportsTo']['email']

    def get_reports_to_id(self, employee_id):
        '''Takes employee ID, returns the ID who the employee reports to'''
        info = self.get_employee(employee_id)
        dict = json.loads(info)
        return dict['work']['reportsTo']['id']
