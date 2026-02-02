$headers = @{
    'Origin' = 'https://thc-toolbox-frontend.vercel.app'
}

$response = Invoke-WebRequest `
    -Uri "https://thc-toolbox-backend.vercel.app/health" `
    -UseBasicParsing `
    -Headers $headers

Write-Host "Status: $($response.StatusCode)"
Write-Host ""
Write-Host "CORS Headers:"
$response.Headers | Where-Object { $_ -like "*Access-Control*" -or $_ -like "*Origin*" } | ForEach-Object {
    Write-Host "$_`t$($response.Headers[$_])"
}
