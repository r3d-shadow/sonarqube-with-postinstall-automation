import requests
import time
import os
import json
import datetime
from dotenv import load_dotenv
load_dotenv()

# Set the SonarQube URL and credentials
sonarqube_path = os.getenv('SONAR_WEB_CONTEXT')
sonarqube_name = os.getenv('SONARQUBE_NAME')
sonarqube_url = f'http://{sonarqube_name}:9000{sonarqube_path}'
admin_username = 'admin'
admin_password = os.getenv('SONARQUBE_CURRENT_PASSWORD')
new_password = os.getenv('SONARQUBE_NEW_PASSWORD')
generated_tokens = {}
session = requests.Session()
proxies = {
    'http': 'http://localhost:8080',
}
# session.proxies.update(proxies)

# Calculate the expiration date as current date + 3 months
current_date = datetime.datetime.now()
token_expiration_date = (current_date + datetime.timedelta(days=3*30)).strftime('%Y-%m-%d')


def change_password():
    api_endpoint = f'{sonarqube_url}/api/users/change_password'
    payload = {
        'login': admin_username,
        'previousPassword': admin_password,
        'password': new_password
    }

    response = requests.post(api_endpoint, data=payload, auth=(admin_username, admin_password))
    if response.status_code == 204:
        print('Admin password changed successfully!')
    else:
        print(f'Failed to change admin password. Status code: {response.status_code}')

def login():
    api_endpoint = f'{sonarqube_url}/api/authentication/login'

    data = {
        'login': admin_username,
        'password': new_password
    }

    response = session.post(api_endpoint, data=data)
    print(response.headers)

    if response.status_code == 200:
        print('User authenticated successfully!')
    else:
        print(f'Failed to authenticate user. Status code: {response.status_code}')

def create_project(project_name):
    create_project_endpoint = f'{sonarqube_url}/api/projects/create'

    project_data = {
        'name': project_name,
        'project': project_name,
        'visibility': 'private',
        'mainBranch': 'main'
    }
    xsrf_token = session.cookies.get('XSRF-TOKEN')
    headers = {
        'X-XSRF-TOKEN': xsrf_token,
    }

    create_project_response = session.post(create_project_endpoint, data=project_data, headers=headers)
    print(create_project_response.text)

    if create_project_response.status_code == 200:
        print(f'Project "{project_name}" created successfully!')
        return True
    else:
        print(f'Failed to create project. Status code: {create_project_response.status_code}')
        return False

def token_generation(token_name, projectKey):
    token_generation_endpoint = f'{sonarqube_url}/api/user_tokens/generate'

    token_data = {
        'name': token_name,
        'type': 'PROJECT_ANALYSIS_TOKEN',
        'projectKey': projectKey,
        'expirationDate': token_expiration_date
    }
    xsrf_token = session.cookies.get('XSRF-TOKEN')
    headers = {
        'X-XSRF-TOKEN': xsrf_token,
    }
    token_generation_response = session.post(token_generation_endpoint, data=token_data,  headers=headers)
    print(token_generation_response.text)

    if token_generation_response.status_code == 200:
        token = token_generation_response.json()
        generated_tokens[token_name] = token['token']
        print(f'Token generated successfully')
    else:
        print(f'Failed to generate token. Status code: {token_generation_response.status_code}')

def token_deletion(token_name):
    token_deletion_endpoint = f'{sonarqube_url}/api/user_tokens/revoke'

    token_data = {
        'name': token_name,
    }
    xsrf_token = session.cookies.get('XSRF-TOKEN')
    headers = {
        'X-XSRF-TOKEN': xsrf_token,
    }
    token_deletion_response = session.post(token_deletion_endpoint, data=token_data,  headers=headers)

    if token_deletion_response.status_code == 204:
        print(f'Token deleted successfully: {token_name}')
    else:
        print(f'Failed to deleted token. Status code: {token_deletion_response.status_code}')


def quality_gate(quality_gate_name):
    quality_gate_generation_endpoint = f'{sonarqube_url}/api/qualitygates/create'

    quality_gate_data = {
        'name': quality_gate_name,
    }
    xsrf_token = session.cookies.get('XSRF-TOKEN')
    headers = {
        'X-XSRF-TOKEN': xsrf_token,
    }
    quality_gate_generation_response = session.post(quality_gate_generation_endpoint, data=quality_gate_data,  headers=headers)
    
    if quality_gate_generation_response.status_code == 200:
        print(f'Quality Gate generated successfully')
    else:
        print(f'Failed to generate Quality Gate. Status code: {quality_gate_generation_response.status_code}')

def quality_gate_update_coverage_conditions(quality_gate_name, coverage_threshold, duplicated_lines_density_threshold):
    quality_gate_details_endpoint = f'{sonarqube_url}/api/qualitygates/show'
    params = {
        'name': quality_gate_name
    }
    quality_gate_details_response = session.get(quality_gate_details_endpoint, params=params)

    for condition in quality_gate_details_response.json().get('conditions', []):
        if condition.get('metric') == 'new_coverage':
            condition['error'] = coverage_threshold
        elif condition.get('metric') == 'new_duplicated_lines_density':
            condition['error'] = duplicated_lines_density_threshold
            
        quality_gate_updation_endpoint = f'{sonarqube_url}/api/qualitygates/update_condition'
        xsrf_token = session.cookies.get('XSRF-TOKEN')
        headers = {
            'X-XSRF-TOKEN': xsrf_token,
        }
        quality_gate_updation_response = session.post(quality_gate_updation_endpoint, data=condition, headers=headers)
    
    quality_gate_data = {
        'name': quality_gate_name,
    }
    quality_gate_set_default_endpoint = f'{sonarqube_url}/api/qualitygates/set_as_default'
    quality_gate_set_default_response = session.post(quality_gate_set_default_endpoint, data=quality_gate_data, headers=headers)
    
    if quality_gate_set_default_response.status_code == 204:
        print(f'Quality Gate set as default')
    else:
        print(f'Failed to set as default Quality Gate. Status code: {quality_gate_set_default_response.status_code}')

change_password()
login()

with open('config.json', 'r') as f:
    config = json.load(f)

for project in config['projects']:
    create_project(project)
    token_deletion(project)
    token_generation(project, project)

with open('out.json', 'w') as json_file:
    json.dump(generated_tokens, json_file, indent=4)

quality_gate_name = config['quality_gate']['name']
coverage_threshold = config['quality_gate']['coverage_threshold']
duplicated_lines_density_threshold = config['quality_gate']['duplicated_lines_density_threshold']

quality_gate(quality_gate_name)
quality_gate_update_coverage_conditions(quality_gate_name, coverage_threshold, duplicated_lines_density_threshold)