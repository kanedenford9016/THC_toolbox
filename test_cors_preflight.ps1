$response = Invoke-WebRequest `
    -Uri 'https://thc-toolbox-backend.vercel.app/auth/login' `
    -Method OPTIONS `
    -UseBasicParsing `
    -Headers @{
        'Origin' = 'https://thc-toolbox-frontend.vercel.app'
        'Access-Control-Request-Method' = 'POST'
        'Access-Control-Request-Headers' = 'Content-Type'
    }

Write-Host "Status: $($response.StatusCode)"
Write-Host ""
Write-Host "CORS Headers:"
foreach ($header in $response.Headers.Keys | Sort-Object) {
    if ($header -like '*Access-Control*' -or $header -like '*Origin*') {
        Write-Host "$header`: $($response.Headers[$header])"
    }
}
