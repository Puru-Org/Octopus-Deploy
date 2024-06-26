#
# This script is being in test to print the destination values if variable already exist
#
import json
import requests

def extract_and_add_variable(source_json, dest_json, variable_names):
    if source_json.startswith("http"):
        source_data = requests.get(source_json).json()
    else:
        with open(source_json, 'r') as f:
            source_data = json.load(f)

    with open(dest_json, 'r') as f:
        dest_data = json.load(f)

    for variable_name in variable_names:
        existing_variables = [variable for variable in dest_data["Variables"] if variable["Name"] == variable_name]
        if existing_variables:
            existing_variable = existing_variables[0]
            print(f"Variable '{variable_name}' already exists in the destination '{dest_json}' file with Value: {existing_variable['Value']}")
            #print(f"Value: {existing_variable['Value']}")
            #print(f"Scope: {existing_variable['Scope']}")
        else:
            print("Adding the Variable property block to the destination JSON file")
            extracted_data = []
            for variable in source_data:
                if variable.get("Name") == variable_name:
                    extracted_data.append(variable)

            dest_data["Variables"].extend(extracted_data)

    with open(dest_json, 'w') as f:
        json.dump(dest_data, f, indent=2)

# Read source data from file
with open("${{ inputs.source_data }}", 'r') as f:
    source_data = json.load(f)

# Process each source data entry
for data_entry in source_data:
    source_json = data_entry["source_json"]
    variable_names = data_entry["variable_names"]
    dest_json = "${{ inputs.dest_json }}"  # Assuming same destination JSON file for all sources

    # Call function to extract and add variables to destination JSON
    if data_entry.get("copy_all"):
        all_variables = requests.get(source_json).json()
        variable_names.extend(variable["Name"] for variable in all_variables)

    extract_and_add_variable(source_json.strip(), dest_json, variable_names)
