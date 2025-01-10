import requests
from collections import defaultdict

# First, create an API key in Metabase. You need to go to settings->Admin-->authentication->API keys and create a new key associated with the Administrator group
MB_API_KEY = 'mb_cSiPDogjJJxDjhD9jNnGHPLt+7T+Au5K8wrpaBWZiLo=' # You API key goes here
MB_SITE_URL = 'https://staging-chg-healthcare.metabaseapp.com' # Your Metabase URL goes here

# Endpoints
group_endpoint = f'{MB_SITE_URL}/api/permissions/group'
jwt_group_mapping_endpoint = f'{MB_SITE_URL}/api/setting/jwt-group-mappings'
permissions_graph_endpoint = f'{MB_SITE_URL}/api/permissions/graph'
graph_group_endpoint = f'{MB_SITE_URL}/api/permissions/graph/group'
properties_endpoint = f'{MB_SITE_URL}/api/session/properties'

def db_names():
    t = [('Sample Database', ''), ('Oneview QA', ''), ('Oneview Prod', ''), ('OneView DW', '')]
    return dict(t)

def get_current_groups():
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    response = requests.get(properties_endpoint, headers=headers)
    if response.status_code == 200:
        properties = response.json()
        return properties['jwt-group-mappings']
    else:
        print(f"Failed to get groups. Status code: {response.status_code}, Response: {response.text}")
        return []

def create_group(group_name):
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    data = {
        'name': group_name
    }
    response = requests.post(group_endpoint, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Group '{group_name}' created successfully with ID {response.json()['id']}")
    else:
        print(f"Failed to create group '{group_name}'. Status code: {response.status_code}, Response: {response.text}")
    return response.json()['id']

def map_group_to_jwt(current_groups, group_id, jwt_group):
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    # start with a copy of the existing mappings
    data = {
        "value": current_groups.copy()
    }

    # if the jwt group key already exists, append the new group id to its list
    if jwt_group in data["value"]:
        if group_id not in data["value"][jwt_group]:
            data["value"][jwt_group].append(group_id)
    # if the jwt group key does not exist, add it with the new group id
    else:
        data["value"][jwt_group] = [group_id]

    print(f"Current groups: {current_groups}")
    print(f"Updated groups: {data}")
    response = requests.put(jwt_group_mapping_endpoint, headers=headers, json=data)
    if response.status_code == 204:
        print(f"Group '{jwt_group}' successfully mapped to JWT group '{jwt_group}'")
    else:
        print(
            f"Failed to map group '{jwt_group}' to JWT group '{jwt_group}'. Status code: {response.status_code}, Response: {response.text}")
def _get_group_name(group_id):
    group_id_endpoint = f'{group_endpoint}/{group_id}'
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    response = requests.get(group_id_endpoint, headers=headers)
    return response.json()['name']

# Prints out DB permissions for all existing groups
def get_group_permissions():
    group_permissions = defaultdict(db_names)
    d = defaultdict(str)
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    response = requests.get(permissions_graph_endpoint, headers=headers)
    if response.status_code == 200:
        print('Getting all group permissions..\n')
        for id in response.json()['groups']:
            d[id] = _get_group_name(id)
            name = _get_group_name(id) + ' (' + str(id) + ')'
            db_permissions = response.json()['groups'][id]
            group_permissions[name]['Sample Database'] = db_permissions['1']
            group_permissions[name]['Oneview QA'] = db_permissions['34']
            group_permissions[name]['Oneview Prod'] = db_permissions['100']
            group_permissions[name]['OneView DW'] = db_permissions['133']

        sorted_gp = dict(sorted(group_permissions.items()))

        for group_name in sorted_gp:
            print(group_name)
            for db in sorted_gp[group_name]:
                print('\t', db, ': ', sorted_gp[group_name][db] if len(sorted_gp[group_name][db]) != 0 else 'No settings enabled')
    else:
        print(f'Failed to retrieve group permissions, Response: {response.text}')

    return d

def get_graph_group_permissions(group_id):
    a = f'{graph_group_endpoint}/{group_id}'
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    response = requests.get(a, headers=headers)
    print(response.json())

# Set permissions for all databases to No self-service
def update_group_permissions(group_id):
    headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': MB_API_KEY
    }
    data = {
        'revision': 142,
        'groups': {
        group_id: {
            "34": {"view-data": "legacy-no-self-service"},
            "100": {"view-data": "legacy-no-self-service"},
            "133": {"view-data": "legacy-no-self-service"},
            "1": {"view-data": "legacy-no-self-service"},
        }
    }
    }
    response = requests.put(permissions_graph_endpoint, headers=headers, json=data)
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Failed to update group ID '{group_id}'. Status code: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    test_groups = ['test_group2', 'test_group3']

    for group_name in test_groups:
        current_groups = get_current_groups()
        group_id = create_group(group_name)
        map_group_to_jwt(current_groups, group_id, group_name)

    # get_graph_group_permissions(275)
    # update_group_permissions(275)
