# Check if the weather Lambda has the API key configured

Write-Host "Checking Weather Lambda Environment Variables..." -ForegroundColor Cyan
Write-Host ""

# Get the Lambda function name from the stack
$functionName = aws cloudformation describe-stack-resources `
  --stack-name smart-rural-ai `
  --region ap-south-1 `
  --query "StackResources[?LogicalResourceId=='WeatherFunction'].PhysicalResourceId" `
  --output text

if ([string]::IsNullOrEmpty($functionName)) {
  Write-Host "❌ Could not find WeatherFunction in stack" -ForegroundColor Red
  exit 1
}

Write-Host "✅ Found Lambda: $functionName" -ForegroundColor Green
Write-Host ""

# Get environment variables
Write-Host "Environment Variables:" -ForegroundColor Yellow
aws lambda get-function-configuration `
  --function-name $functionName `
  --region ap-south-1 `
  --query 'Environment.Variables' `
  --output json

Write-Host ""
Write-Host "Checking if OPENWEATHER_API_KEY is set..." -ForegroundColor Yellow
$apiKey = aws lambda get-function-configuration `
  --function-name $functionName `
  --region ap-south-1 `
  --query 'Environment.Variables.OPENWEATHER_API_KEY' `
  --output text

if ($apiKey -eq "None" -or [string]::IsNullOrEmpty($apiKey)) {
  Write-Host "❌ OPENWEATHER_API_KEY is NOT set!" -ForegroundColor Red
  Write-Host ""
  Write-Host "To fix this, redeploy the stack:" -ForegroundColor Yellow
  Write-Host "  cd infrastructure"
  Write-Host "  sam build"
  Write-Host "  sam deploy"
} else {
  Write-Host "✅ OPENWEATHER_API_KEY is set: $($apiKey.Substring(0, [Math]::Min(10, $apiKey.Length)))..." -ForegroundColor Green
  Write-Host ""
  Write-Host "Testing the API key with OpenWeatherMap..." -ForegroundColor Yellow
  
  $testUrl = "http://api.openweathermap.org/data/2.5/weather?q=Chennai,IN&appid=$apiKey&units=metric"
  try {
    $response = Invoke-RestMethod -Uri $testUrl
    if ($response.cod -eq 200) {
      Write-Host "✅ API Key is VALID! Weather data retrieved successfully." -ForegroundColor Green
      Write-Host "   Location: $($response.name)"
      Write-Host "   Temperature: $($response.main.temp)°C"
      Write-Host "   Condition: $($response.weather[0].description)"
    } else {
      Write-Host "❌ API returned error code: $($response.cod)" -ForegroundColor Red
      Write-Host "   Message: $($response.message)"
    }
  } catch {
    Write-Host "❌ Failed to test API key: $_" -ForegroundColor Red
  }
}
