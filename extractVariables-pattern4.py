import json

def extract_and_add_variable(source_json, dest_json, variable_names):
    with open(source_json, 'r') as f:
        source_data = json.load(f)

    with open(dest_json, 'r') as f:
        dest_data = json.load(f)

    for variable_name in variable_names:
        existing_variables = [variable["Name"] for variable in dest_data["Variables"]]
        if variable_name in existing_variables:
            print(f"Variable '{variable_name}' already exists in the destination '{dest_json}' file.")
        else:
            print(f"Adding the '{variable_name}' property block to the destination '{dest_json}' file")
            extracted_data = []
            for variable in source_data["Variables"]:
                if variable.get("Name") == variable_name:
                    extracted_data.append(variable)

            dest_data["Variables"].extend(extracted_data)

    with open(dest_json, 'w') as f:
        json.dump(dest_data, f, indent=2)

# Read source data from file
with open("source_data", 'r') as f:
    lines = f.readlines()

# Process each line in source data
for line in lines:
    line = line.strip()
    if line:  # Skip empty lines
        source_json, *variable_names = line.split(",")
        dest_json = "demo-variables.json"  # Assuming same destination JSON file for all sources

        # Call function to extract and add variables to destination JSON
        extract_and_add_variable(source_json, dest_json, variable_names)
