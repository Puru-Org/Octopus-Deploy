import json
import os

def fetch_json_from_file(file_path):
    """Fetch JSON data from a local file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_and_add_variable(source_json_path, project_variable_json, variable_names):
    """Extract specified variables from the source JSON and add them to the destination JSON."""
    source_data = fetch_json_from_file(source_json_path)

    with open(project_variable_json, 'r') as f:
        dest_data = json.load(f)

    # Create a dictionary of destination environments for reference
    dest_environment_list = dest_data["ScopeValues"]["Environments"]
    dest_environment_dict = {env["Id"]: env["Name"] for env in dest_environment_list}

    for variable_name in variable_names:
        # Check if the variable already exists in the destination JSON
        existing_variables = [variable for variable in dest_data["Variables"] if variable["Name"] == variable_name]
        if existing_variables:
            print(f"Variable '{variable_name}' already exists in the destination '{project_variable_json}' file.")
        else:
            print(f"Adding the '{variable_name}' variable property block to the destination '{project_variable_json}' file")
            # Extract the variable from the source data
            extracted_data = [variable for variable in source_data if variable.get("Name") == variable_name]
            dest_data["Variables"].extend(extracted_data)

    # Write the updated destination data back to the file
    with open(project_variable_json, 'w') as f:
        json.dump(dest_data, f, indent=2)

if __name__ == "__main__":
    # Main script execution
    # Read the global reference JSON file path from the environment variable
    global_ref_json_path = os.getenv("GLOBAL_REF_JSON")
    if not global_ref_json_path:
        raise Exception("Environment variable GLOBAL_REF_JSON not set")

    with open(global_ref_json_path, 'r') as f:
        source_data = json.load(f)

    # Process each entry in the global reference JSON
    for data_entry in source_data:
        source_json_path = data_entry["global_variable_path"]
        variable_names = data_entry["variable_names"]
        project_variable_json = os.getenv("PROJECT_VARIABLE_JSON")  # Destination JSON file path

        if not project_variable_json:
            raise Exception("Environment variable PROJECT_VARIABLE_JSON not set")

        # If the "copy_all" flag is set, add all variables from the source JSON
        if data_entry.get("copy_all"):
            all_variables = fetch_json_from_file(source_json_path)
            variable_names.extend(variable["Name"] for variable in all_variables)

        # Extract and add variables to the destination JSON
        extract_and_add_variable(source_json_path.strip(), project_variable_json, variable_names)