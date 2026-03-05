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

if ([string]::IsNullOrWhiteSpace($env:OPENWEATHER_API_KEY) -or $env:OPENWEATHER_API_KEY -eq "CHANGE_ME") {
		throw "OPENWEATHER_API_KEY is missing or set to CHANGE_ME. Set a real key in your shell environment before deploy."
}

Write-Host "========================================="
Write-Host " Smart Rural AI Advisor — CFN Deploy"
Write-Host "========================================="

$templatePath = "infrastructure/template.yaml"
$packagedPath = "infrastructure/packaged-template.yaml"

Write-Host "Packaging CloudFormation template..."
aws cloudformation package `
	--template-file $templatePath `
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
		OpenWeatherApiKey=$($env:OPENWEATHER_API_KEY) `
		EnforceCodePolicy=$EnforceCodePolicy `
		CognitoUserPoolId=$CognitoUserPoolId `
		EnableRateLimitTTL=$EnableRateLimitTTL

Write-Host "Deployment complete."
