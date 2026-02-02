$loginData = @{
    username = "RedDragon2010"
    password = "testpass123"
    torn_api_key = "your_api_key_here"
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "https://thc-toolbox-backend.vercel.app/auth/login" `
    -Method POST `
    -ContentType "application/json" `
    -Body $loginData `
    -UseBasicParsing

$response.Content
