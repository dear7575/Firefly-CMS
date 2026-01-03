# Firefly-CMS 前端本地构建部署脚本
# 用途：在本地构建前端产物，然后手动复制到服务器

$PUBLIC_API_URL = "https://dear7575.cn/api"

Write-Host "1. 开始本地构建前端..." -ForegroundColor Cyan
$env:PUBLIC_API_URL = $PUBLIC_API_URL
$env:NODE_OPTIONS = "--max-old-space-size=4096"

# 执行编译
pnpm build

# 检查编译是否成功
if ($LASTEXITCODE -ne 0)
{
    Write-Host "构建失败，请检查错误。" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "2. 构建完成！" -ForegroundColor Green
Write-Host "提示: 现在你可以将本地的 dist 目录复制到服务器的 Firefly-CMS 目录下。" -ForegroundColor Yellow
Write-Host "建议使用 scp 或 SFTP:" -ForegroundColor White
Write-Host "scp -r ./dist user@your-server-ip:/path/to/Firefly-CMS/" -ForegroundColor Cyan
Write-Host "完成后，请参考 walkthrough.md 中的 Method C 使用挂载方式运行。" -ForegroundColor Yellow
