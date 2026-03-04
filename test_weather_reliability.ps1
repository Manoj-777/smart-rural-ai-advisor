# Test weather API reliability by making multiple requests

param(
    [int]$TestCount = 10,
    [string]$Location = "Chennai"
)

Write-Host "Testing Weather API Reliability" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Yellow
Write-Host "Test Count: $TestCount" -ForegroundColor Yellow
Write-Host ""

$apiUrl = "https://zuadk9l1nc.execute-api.ap-south-1.amazonaws.com/Prod/weather/$Location"
$successCount = 0
$failCount = 0
$timeouts = 0
$errors = @()

for ($i = 1; $i -le $TestCount; $i++) {
    Write-Host "Test $i/$TestCount... " -NoNewline
    
    try {
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 10 -ErrorAction Stop
        $stopwatch.Stop()
        
        if ($response.status -eq "success" -and $response.data) {
            $successCount++
            Write-Host "✅ Success ($($stopwatch.ElapsedMilliseconds)ms)" -ForegroundColor Green
        } else {
            $failCount++
            $errorMsg = if ($response.message) { $response.message } else { "Unknown error" }
            Write-Host "❌ Failed: $errorMsg" -ForegroundColor Red
            $errors += "Test $i : $errorMsg"
        }
    } catch {
        $failCount++
        if ($_.Exception.Message -like "*timeout*") {
            $timeouts++
            Write-Host "⏱️  Timeout" -ForegroundColor Yellow
            $errors += "Test $i : Timeout"
        } else {
            Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
            $errors += "Test $i : $($_.Exception.Message)"
        }
    }
    
    # Small delay between requests
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Results:" -ForegroundColor Cyan
Write-Host "  ✅ Success: $successCount/$TestCount ($([math]::Round($successCount/$TestCount*100, 1))%)" -ForegroundColor Green
Write-Host "  ❌ Failed: $failCount/$TestCount" -ForegroundColor Red
Write-Host "  ⏱️  Timeouts: $timeouts/$TestCount" -ForegroundColor Yellow
Write-Host ""

if ($errors.Count -gt 0) {
    Write-Host "Error Details:" -ForegroundColor Yellow
    $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host ""
}

# Diagnosis
if ($successCount -eq $TestCount) {
    Write-Host "✅ API is working reliably!" -ForegroundColor Green
} elseif ($timeouts -gt $failCount / 2) {
    Write-Host "⚠️  High timeout rate - possible Lambda cold start or network issues" -ForegroundColor Yellow
    Write-Host "   Consider increasing Lambda timeout or adding connection pooling" -ForegroundColor Gray
} elseif ($failCount -gt $TestCount / 2) {
    Write-Host "⚠️  High failure rate - check Lambda logs:" -ForegroundColor Yellow
    Write-Host "   aws logs tail /aws/lambda/smart-rural-ai-WeatherFunction --follow" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Intermittent issues detected" -ForegroundColor Yellow
    Write-Host "   Success rate: $([math]::Round($successCount/$TestCount*100, 1))%" -ForegroundColor Gray
}
