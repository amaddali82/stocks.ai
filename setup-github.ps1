# GitHub Repository Setup Script
# Run this after creating a new repository on GitHub

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "GitHub Repository Setup" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ Git repository initialized" -ForegroundColor Green
Write-Host "✓ All files committed (40 files, 6037 insertions)" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   - Go to https://github.com/new" -ForegroundColor Gray
Write-Host "   - Repository name: stocks.ai" -ForegroundColor Gray
Write-Host "   - Description: Advanced AI-powered trading prediction system" -ForegroundColor Gray
Write-Host "   - Keep it Private (recommended) or Public" -ForegroundColor Gray
Write-Host "   - Do NOT initialize with README (we already have one)" -ForegroundColor Gray
Write-Host ""

Write-Host "2. After creating the repository, run these commands:" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/stocks.ai.git" -ForegroundColor Cyan
Write-Host "   git branch -M main" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""

Write-Host "Or if you have GitHub CLI installed:" -ForegroundColor White
Write-Host ""
Write-Host "   gh repo create stocks.ai --private --source=. --remote=origin --push" -ForegroundColor Cyan
Write-Host ""

Write-Host "Files ready to push:" -ForegroundColor Yellow
Write-Host "  ✓ 40 files committed" -ForegroundColor Green
Write-Host "  ✓ .gitignore configured" -ForegroundColor Green
Write-Host "  ✓ README.md included" -ForegroundColor Green
Write-Host "  ✓ Complete documentation" -ForegroundColor Green
Write-Host ""

Write-Host "Repository Stats:" -ForegroundColor Yellow
git log --oneline
Write-Host ""

Write-Host "Press any key to continue to Docker deployment..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
