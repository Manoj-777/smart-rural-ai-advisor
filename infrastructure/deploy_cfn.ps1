Param(
    [string]$StackName = "smart-rural-ai",
    [string]$Region = "ap-south-1",
    [string]$S3Bucket = "smart-rural-ai-948809294205",
    [string]$BedrockKBId = "9X1YUTXNOQ",
    [string]$EnforceCodePolicy = "true",
    [string]$CognitoUserPoolId = "ap-south-1_X58lNMEcn",
    [string]$EnableRateLimitTTL = "false"
)

$ErrorActionPreference = "Stop"

$openWeatherSecretArn = $env:OPENWEATHER_API_KEY_SECRET_ARN
$openWeatherApiKey = $env:OPENWEATHER_API_KEY

if ([string]::IsNullOrWhiteSpace($openWeatherSecretArn) -and ([string]::IsNullOrWhiteSpace($openWeatherApiKey) -or $openWeatherApiKey -eq "CHANGE_ME")) {
    throw "Provide OPENWEATHER_API_KEY_SECRET_ARN (preferred) or OPENWEATHER_API_KEY in your shell environment before deploy."
}

Write-Host "========================================="
Write-Host " Smart Rural AI Advisor - CFN Deploy"
Write-Host "========================================="

$templatePath = "infrastructure/template.yaml"
$packagedPath = "infrastructure/packaged-template.yaml"
$buildTemplatePath = ".aws-sam/build/template.yaml"

Write-Host "Building SAM application (includes Lambda dependencies from requirements.txt)..."
sam build --template-file $templatePath --no-cached

$gttsBuildPath = ".aws-sam/build/AgentOrchestratorFunction/gtts"
if (-not (Test-Path $gttsBuildPath)) {
    throw "Build verification failed: missing gTTS package at '$gttsBuildPath'. Check backend/lambdas/agent_orchestrator/requirements.txt and rerun deploy."
}
Write-Host "Dependency check passed: gTTS packaged in AgentOrchestrator artifact."

Write-Host "Packaging CloudFormation template..."
aws cloudformation package `
    --template-file $buildTemplatePath `
    --s3-bucket $S3Bucket `
    --output-template-file $packagedPath `
    --region $Region

Write-Host "Deploying stack..."
aws cloudformation deploy `
    --template-file $packagedPath `
    --stack-name $StackName `
    --capabilities CAPABILITY_IAM `
    --region $Region `
    --parameter-overrides `
        BedrockKBId=$BedrockKBId `
        OpenWeatherApiKey=$openWeatherApiKey `
        OpenWeatherApiKeySecretArn=$openWeatherSecretArn `
        EnforceCodePolicy=$EnforceCodePolicy `
        CognitoUserPoolId=$CognitoUserPoolId `
        EnableRateLimitTTL=$EnableRateLimitTTL

Write-Host "Deployment complete."
