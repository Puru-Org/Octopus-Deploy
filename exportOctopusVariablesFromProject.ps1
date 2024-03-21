# Set your Octopus Deploy details
$octopusUrl = "$env:OCTOPUS_SERVER_URL"
$apiKey = "$env:OCTOPUS_API_KEY"
$projectName = "$env:ProjectName"
$spaceName = "Default"
# Define the output JSON file path
$outputFilePath = "variables.json"

# Base64 encode the API key
$base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(":$($apiKey)"))

# Function to make REST API requests
function Invoke-OctopusApi {
    param (
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null
    )

    $headers = @{
        Authorization = "Basic $base64AuthInfo"
    }

    $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $headers -ContentType "application/json" -Body $Body
    return $response
}
# Get space
$spaceList = Invoke-RestMethod "$octopusURL/api/spaces/all" -Headers $header
$space = $spaceList | Where-Object { $_.Name -eq $spaceName }

# Get destination project
$projectList = Invoke-RestMethod "$octopusURL/api/$($space.Id)/projects/all" -Headers $header
$sourceProject = $projectList | Where-Object { $_.Name -eq $projectName }
$sourceProjectVariableSetId = $sourceProject.VariableSetId

# Get all variables and library variable sets
$variablesUrl = "$octopusURL/api/$($space.Id)/variables/$sourceProjectVariableSetId"

##$variablesUrl = "$octopusUrl/api/variables/$projectName/$sourceProjectVariableSetId"
$variablesResponse = Invoke-OctopusApi -Url $variablesUrl
# Get all variables and library variable sets
$variablesUrl = "$octopusUrl/api/variables/$projectName/all"
$variablesResponse = Invoke-OctopusApi -Url $variablesUrl

# Store variables in a hashtable
$variables = @{}

# Iterate through variable sets and store variables
foreach ($variableSet in $variablesResponse.VariableSet) {
    $variables[$variableSet.Id] = @{
        Name = $variableSet.Name
        Variables = $variableSet.Variables
    }
}

# Convert hashtable to JSON and save to file
$variables | ConvertTo-Json | Out-File -FilePath $outputFilePath

Write-Host "Variables have been extracted and saved to $outputFilePath"