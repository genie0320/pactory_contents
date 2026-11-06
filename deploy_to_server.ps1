param(
    [switch]$InstallDeps = $false
)

$ServerUser = "user"
$ServerIP = "192.168.55.196"
$RemoteDir = "~/pactory_contents"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  [Pactory Seed Engine] 코드 배포 도구 (Windows -> Server)" -ForegroundColor Cyan
Write-Host ("  대상 서버: " + $ServerUser + "@" + $ServerIP) -ForegroundColor Cyan
Write-Host "========================================================"

# 1. 임시 배포용 압축 파일 생성 (데이터, 캐시, 가상환경, .env 완전 제외)
Write-Host "[1/4] 배포용 소스코드 패키징 중..." -ForegroundColor Yellow
$tempArchive = "deploy_code_tmp.tar.gz"
if (Test-Path $tempArchive) { Remove-Item $tempArchive -Force }

& tar --exclude="__pycache__" --exclude="*.pyc" --exclude=".pytest_cache" -czf $tempArchive src config.yaml pyproject.toml run.py scripts

if (-not (Test-Path $tempArchive)) {
    Write-Host "  [오류] 배포 압축 파일 생성 실패." -ForegroundColor Red
    exit 1
}

# 2. 서버로 전송
Write-Host "[2/4] 서버로 최신 코드 전송 중..." -ForegroundColor Yellow
$remoteDest = "${ServerUser}@${ServerIP}:${RemoteDir}/deploy_code_tmp.tar.gz"
scp -o BatchMode=yes -o ConnectTimeout=5 $tempArchive $remoteDest
Remove-Item $tempArchive -Force

# 3. 서버에서 압축 해제 및 서비스 재시작
Write-Host "[3/4] 서버 소스코드 갱신 및 웹 서비스 재기동..." -ForegroundColor Yellow
$remoteCmd = "cd ~/pactory_contents && tar -xzf deploy_code_tmp.tar.gz && rm deploy_code_tmp.tar.gz && chmod +x scripts/*.sh && cp scripts/*.service scripts/*.timer ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now pactory-indexer.timer pactory-backup.timer"
if ($InstallDeps) {
    $remoteCmd += " && .venv/bin/pip install -e ."
}
$remoteCmd += " && systemctl --user restart pactory-studio.service"

ssh -o BatchMode=yes -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" $remoteCmd

# 4. 서비스 상태 검증
Write-Host "[4/4] 서버 서비스 상태 검증 중..." -ForegroundColor Yellow
$status = ssh -o BatchMode=yes -o ConnectTimeout=5 "${ServerUser}@${ServerIP}" "systemctl --user is-active pactory-studio.service"
if ($status.Trim() -eq "active") {
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  [배포 성공!] 최신 코드가 서버에 즉시 반영되었습니다." -ForegroundColor Green
    Write-Host "  웹 스튜디오: http://${ServerIP}:8501" -ForegroundColor Green
    Write-Host "========================================================"
} else {
    Write-Host "  [주의] 서비스 재기동 상태를 확인하세요: $status" -ForegroundColor Red
}
