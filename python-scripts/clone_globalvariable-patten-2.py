import json
import requests
import os
import base64

def fetch_json_from_raw_url(raw_url):
    headers = {
        'Authorization': f'token {os.getenv("GH_TOKEN")}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    try:
        response = requests.get(raw_url, headers=headers)
        response.raise_for_status()
        content = response.json()
        if 'content' in content:
            return json.loads(base64.b64decode(content['content']).decode('utf-8'))
        else:
            print(f"No content found at URL '{raw_url}'")
            return None
    except requests.RequestException as e:
        print(f"Error fetching JSON from API URL '{raw_url}': {e}")
        return None
    # response = requests.get(raw_url, headers=headers)
    # if response.status_code != 200:
    #     raise Exception(f"Error fetching JSON from URL '{raw_url}': {response.status_code} {response.reason}")
    # return response.json()

def extract_and_add_variable(source_json_url, project_variable_json, variable_names):
    source_data = fetch_json_from_raw_url(source_json_url)

    with open(project_variable_json, 'r') as f:
        dest_data = json.load(f)

    dest_environment_list = dest_data["ScopeValues"]["Environments"]
    dest_environment_dict = {env["Id"]: env["Name"] for env in dest_environment_list}

    for variable_name in variable_names:
        existing_variables = [variable for variable in dest_data["Variables"] if variable["Name"] == variable_name]
        if variable_name in existing_variables:
            print(f"Variable '{variable_name}' already exists in the destination '{project_variable_json}' file.")
        else:
            print(f"Adding the '{variable_name}' Variable property block to the destination '{project_variable_json}' file")
            extracted_data = [variable for variable in source_data if variable.get("Name") == variable_name]

            dest_data["Variables"].extend(extracted_data)

    with open(project_variable_json, 'w') as f:
        json.dump(dest_data, f, indent=2)

# Read source data from environment variable
global_ref_json_path = os.getenv("GLOBAL_REF_JSON")
with open(global_ref_json_path, 'r') as f:
    source_data = json.load(f)

# Process each source data entry
for data_entry in source_data:
    source_json_url = data_entry["global_variable_json_url"]
    variable_names = data_entry["variable_names"]
    project_variable_json = os.getenv("PROJECT_VARIABLE_JSON")  # Assuming same destination JSON file for all sources

    # Call function to extract and add variables to destination JSON
    if data_entry.get("copy_all"):
        all_variables = fetch_json_from_raw_url(source_json_url)
        variable_names.extend(variable["Name"] for variable in all_variables)

    extract_and_add_variable(source_json_url.strip(), project_variable_json, variable_names)