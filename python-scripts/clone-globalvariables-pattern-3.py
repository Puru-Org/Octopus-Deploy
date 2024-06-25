import json
import requests
import base64

# Your GitHub token
GITHUB_TOKEN = ''

# Headers for GitHub API requests
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'X-GitHub-Api-Version': '2022-11-28'
}

# Load global_var_ref.json
with open('D:\Puru\Octopus\Puru-Org\Octopus-CD\Octopus\global_ref.json', 'r') as f:
    global_var_refs = json.load(f)

# Load existing project variables from project_variable.json
with open('D:\Puru\Octopus\Puru-Org\Octopus-CD\Octopus\demo-variables.json', 'r') as f:
    project_variables = json.load(f)

# Function to fetch variables from URL
def fetch_variables(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        # Decode the base64 content
        file_content = base64.b64decode(content["content"]).decode('utf-8')
        json_content = json.loads(file_content)
        # Handle if json_content is a list or a dictionary
        if isinstance(json_content, list):
            return json_content
        elif isinstance(json_content, dict):
            return json_content.get("Variables", [])
        else:
            return []
    else:
        print(f"Failed to fetch variables from {url}, status code: {response.status_code}")
        return []

# Initialize a list to collect all source variables
all_source_variables = []

# Process each reference in global_var_refs
for ref in global_var_refs:
    url = ref["global_variable_json_url"]
    source_variables = fetch_variables(url)
    all_source_variables.extend(source_variables)

# Convert list of source variables to a dictionary for easier access
source_variable_dict = {var['Name']: var for var in all_source_variables}

# Retrieve the list of project variables
project_variable_list = project_variables.get("Variables", [])

# Process each source variable
for source_variable in all_source_variables:
    source_name = source_variable["Name"]
    source_value = source_variable["Value"]
    source_scope_environments = source_variable.get("Scope", {}).get("Environment", [])

    # Initialize flag to check if source_variable exists in project_variables
    found_in_project = False

    # Process each existing project variable
    for project_variable in project_variable_list:
        project_name = project_variable["Name"]
        project_value = project_variable["Value"]
        project_scope_environments = project_variable.get("Scope", {}).get("Environment", [])
     
        # Check if source_name and source_value match project_variable's Name and Value
        if source_name == project_name and source_value == project_value:
            found_in_project = True

            # Check if source_scope_environments match project_variable's Scope.Environment
            if set(source_scope_environments) == set(project_scope_environments):
                print(f"Variable '{source_name}' with value '{source_value}' and environment details '{source_scope_environments}' already exists.")
            elif source_name == project_name and source_value == project_value:
                print(f"WARNING: Variable '{source_name}' has different scopes.")
                print(f"Project scopes: {project_scope_environments}, Source scopes: {source_scope_environments}")
                update_scopes = input(f"Do you want to update the scopes for variable '{source_name}'? (yes/no): ").strip().lower()
                if update_scopes == 'yes':
                    project_variable["Scope"]["Environment"] = source_scope_environments
                    print(f"Scopes updated for variable '{source_name}'")
        

            # No need to check further once found and processed
            break

    # If source_variable was not found in project_variables, add it
    if not found_in_project:
        new_variable = {
            "Name": source_name,
            "Value": source_value,
            "Scope": source_variable.get("Scope", {})
        }
        project_variable_list.append(new_variable)
        print(f"Added new variable '{source_name}'")

# Write the updated variables to project_variable.json
with open('D:\Puru\Octopus\Puru-Org\Octopus-CD\Octopus\demo-variables.json', 'w') as f:
    json.dump(project_variables, f, indent=4)

print("Variables have been added/updated in project_variable.json")
