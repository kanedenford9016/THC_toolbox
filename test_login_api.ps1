$body = @{
    username = "RedDragon2010"
    password = "testpass123"
    torn_api_key = "my_api_key_here"
} | ConvertTo-Json

Write-Host "Testing login to: https://thc-toolbox-backend.vercel.app/auth/login"
Write-Host "Request body: $body"
Write-Host ""

try {
    $response = Invoke-WebRequest `
        -Uri "https://thc-toolbox-backend.vercel.app/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing `
        -Headers @{'Origin' = 'https://thc-toolbox-frontend.vercel.app'}

    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response:`n$($response.Content)"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
    Write-Host "Response: $($_.Exception.Response.Content)"
}
