# Build the React frontend and copy it to the FastAPI backend dist directory
Write-Host "1. Building React Frontend..." -ForegroundColor Cyan
Set-Location frontend
npm install
npm run build
Set-Location ..

Write-Host "2. Preparing backend dist folder..." -ForegroundColor Cyan
if (Test-Path github_qa_bot/dist) {
    Remove-Item -Recurse -Force github_qa_bot/dist
}

Write-Host "3. Copying frontend build output to github_qa_bot/dist..." -ForegroundColor Cyan
Copy-Item -Recurse -Force frontend/dist github_qa_bot/dist

Write-Host "Success! Frontend has been built and copied to the backend." -ForegroundColor Green
Write-Host "You can now commit changes to Git and push to deploy to Render Free Tier." -ForegroundColor Yellow
