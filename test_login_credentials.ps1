$body = @{
    username = "RedDragon2010"
    password = "YouShallNotPass2026"
    torn_api_key = "vdtGSukfoVMDqmp5"
} | ConvertTo-Json

Write-Host "Testing login with provided credentials..."
Write-Host ""

try {
    $response = Invoke-WebRequest `
        -Uri "https://thc-toolbox-backend.vercel.app/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing

    Write-Host "✅ Login successful!"
    Write-Host "Status: $($response.StatusCode)"
    Write-Host ""
    Write-Host "Response:"
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    if ($_.Exception.Response) {
        Write-Host "❌ Login failed"
        Write-Host "Status: $($_.Exception.Response.StatusCode)"
        Write-Host ""
        Write-Host "Error response:"
        Write-Host $_.Exception.Response.StatusCode.value__
        Write-Host ""
        try {
            $errorContent = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorContent)
            $errorBody = $reader.ReadToEnd()
            Write-Host $errorBody | ConvertFrom-Json | ConvertTo-Json
        } catch {
            Write-Host $_.Exception.Message
        }
    } else {
        Write-Host "❌ Request failed: $($_.Exception.Message)"
    }
}
