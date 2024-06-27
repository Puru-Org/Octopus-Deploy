# Define variables
# Powershell script will add the variables into the Octopus project
# It handles variables with both environment and role scopes, as well as those without any scope definitions.

$octopusURL = "${{ github.event.inputs.octopus_url }}"
$apiKey = "${{ secrets.OCTOPUS_API_KEY }}"
#$apiKey = "${{ secrets[inputs.octopusApiName] }}"
#$sourceVariableFile = "${{ inputs.variableFilePath }}"
$sourceVariableFile = $env:variableFilePath
$projectName = "${{ inputs.ProjectName }}"
$spaceName = "Default"
$header = @{ 
    "X-Octopus-ApiKey" = $apiKey
    "Content-Type" = "application/json" 
}

# Function to get environment ID by name
function Get-EnvironmentIdByName {
    param (
        [string]$environmentName,
        [array]$environmentList
    )

    foreach ($env in $environmentList) {
        if ($env.Name -eq $environmentName) {
            return $env.Id
        }
    }
    return $null
}

# Function to get environment name by ID
function Get-EnvironmentNameById {
    param (
        [string]$environmentId,
        [array]$environmentList
    )

    foreach ($env in $environmentList) {
        if ($env.Id -eq $environmentId) {
            return $env.Name
        }
    }
    return $null
}

try {
    $spaces = Invoke-RestMethod -Method Get -Uri "$octopusURL/api/spaces/all" -Headers $header
    if (-not $spaces) {
        throw "Failed to retrieve spaces from Octopus Deploy."
    }
} catch {
    Write-Error "Error retrieving spaces: $_"
    exit 1
}

$space = $spaces | Where-Object { $_.Name -eq $spaceName }
if (-not $space) {
    Write-Error "Space '$spaceName' not found."
    exit 1
}

# Get environment list
try {
    $destinationEnvironmentList = Invoke-RestMethod -Method Get -Uri "$octopusURL/api/$($space.Id)/environments/all" -Headers $header
    if (-not $destinationEnvironmentList) {
        throw "Failed to retrieve environments from Octopus Deploy."
    }
} catch {
    Write-Error "Error retrieving environments: $_"
    exit 1
}

# Get destination project
try {
    $projects = Invoke-RestMethod -Method Get -Uri "$octopusURL/api/$($space.Id)/projects/all" -Headers $header
    if (-not $projects) {
        throw "Failed to retrieve projects from Octopus Deploy."
    }
} catch {
    Write-Error "Error retrieving projects: $_"
    exit 1
}

$project = $projects | Where-Object { $_.Name -eq $projectName }
if (-not $project) {
    Write-Error "Project '$projectName' not found."
    exit 1
}

# Get project variables
$projectVariables = Invoke-RestMethod -Method Get -Uri "$octopusURL/api/$($space.Id)/projects/$($project.Id)/variables" -Headers $header
if (-not $projectVariables) {
    Write-Error "Failed to retrieve project variables from Octopus Deploy."
    exit 1
}

# Ensure the Variables property is initialized
if (-not $projectVariables.Variables) {
    $projectVariables.Variables = @()
}

# Clear existing variables
$projectVariables.Variables = @()

# Load source variable file
$sourceVariables = Get-Content -Path $sourceVariableFile | ConvertFrom-Json
if (-not $sourceVariables) {
    Write-Error "Failed to load source variables from file '$sourceVariableFile'."
    exit 1
}

# Track errors
$errorOccurred = $false

try {
    # Process each source variable
    foreach ($sourceVariable in $sourceVariables.Variables) {
        $name = $sourceVariable.Name
        $value = $sourceVariable.Value
        $description = $sourceVariable.Description
        $type = $sourceVariable.Type
        $scopeEnvironments = $sourceVariable.Scope.Environment
        $scopeRoles = $sourceVariable.Scope.Role
        
        # Proceed only if Role scope is defined
        # if ($null -eq $scopeRoles -or $scopeRoles.Count -eq 0) {
        #     Write-Output "Skipping variable '$name' with '$value' because it does not have Role scope."
        #     continue
        # }

        # Check for sensitive variables
        if ($sourceVariable.IsSensitive -eq $true) {
            Write-Host "Warning: Setting sensitive value for $($name) to DUMMY VALUE" -ForegroundColor Yellow
            $value = "DUMMY VALUE"
        }

        # Check for account type variables
        if ($sourceVariable.Type -match ".*Account") {
            Write-Host "Warning: Cannot convert account type to destination account. Setting to DUMMY VALUE" -ForegroundColor Yellow
            $value = "DUMMY VALUE"
        }

        # Check for certificate type variables
        if ($sourceVariable.Type -match ".*Certificate") {
            Write-Host "Warning: Cannot convert certificate type to destination certificate. Setting to DUMMY VALUE" -ForegroundColor Yellow
            $value = "DUMMY VALUE"
        }

        # Map environment names to their IDs
        $environmentIds = @()
        foreach ($envName in $scopeEnvironments) {
            $envId = Get-EnvironmentIdByName -environmentName $envName -environmentList $destinationEnvironmentList
            if ($envId) {
                $environmentIds += $envId
            } else {
                Write-Error "Environment name '$envName' not found in destination environment list."
                $errorOccurred = $true
            }
        }

        # Only add the variable if no errors occurred
        if (-not $errorOccurred) {
            # Create new variable
            $newVariable = @{
                "Name" = $name
                "Value" = $value
                "Description" = $description
                "Scope" = @{
                    Environment = $environmentIds
                }
                "Type"  = $type
                
            }

            # Include Role scope if it exists
            if ($scopeRoles) {
                Write-Output "The variable '$name' with the value '$value' has a Role scope and is being added..."
                $newVariable.Scope.Role = $scopeRoles
            }

            # Add new variable to project variables
            $projectVariables.Variables += [PSCustomObject]$newVariable
            Write-Output "Added new variable '$name' with value '$value' in environments: $($scopeEnvironments -join ', ')"
        }
    }

    # Update the project variables if no errors occurred
    if (-not $errorOccurred) {
        Write-Host "Saving variables to $octopusURL$($project.Links.Variables)"
        $jsonBody = $projectVariables | ConvertTo-Json -Depth 10
        Write-Output $jsonBody  # Output the JSON body for debugging
        Invoke-RestMethod -Method Put -Uri "$octopusURL$($project.Links.Variables)" -Headers $header -Body $jsonBody
        Write-Output "Project variables updated successfully."
    } else {
        Write-Error "Errors occurred during variable processing. Aborting update."
    }
}
catch {
    Write-Error "Failed to update project variables. Error: $_"
}