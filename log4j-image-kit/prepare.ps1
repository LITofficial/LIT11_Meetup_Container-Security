$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force ".\images" | Out-Null
foreach ($name in @("vulnerable", "patched")) {
    if (Test-Path ".\images\$name.tar") { throw "Existing archive: images/$name.tar. Move it before running again." }
}
$items = @(
    @{ Name = "vulnerable"; Version = "2.14.1" },
    @{ Name = "patched"; Version = "2.24.3" }
)
$metadata = @()
foreach ($item in $items) {
    $tag = "lit11-log4j:$($item.Name)"
    docker build -f Dockerfile --build-arg "LOG4J_VERSION=$($item.Version)" -t $tag .
    if ($LASTEXITCODE -ne 0) { throw "Image build failed: $tag" }
    docker image save -o ".\images\$($item.Name).tar" $tag
    if ($LASTEXITCODE -ne 0) { throw "Image save failed: $tag" }
    $raw = docker image inspect $tag
    if ($LASTEXITCODE -ne 0) { throw "Image inspect failed: $tag" }
    $info = ($raw -join "`n") | ConvertFrom-Json
    $metadata += [PSCustomObject]@{
        tag = $tag
        log4j_version = $item.Version
        image_id = $info[0].Id
        archive_sha256 = (Get-FileHash -Algorithm SHA256 ".\images\$($item.Name).tar").Hash
    }
}
$metadata | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 ".\images\metadata.json"
Write-Host "Done. Images were built and saved, NOT started."
