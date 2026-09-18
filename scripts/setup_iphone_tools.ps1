[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$releaseTag = "v20260913-74585f8"
$assetName = "libimobile-suite-latest_w64.zip"
$expectedHash = (
    "05AA89FC50C89D3E846760A07A1C0159FD" +
    "C56FCA136E58D088EF5D7F600184D6"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolDirectory = Join-Path $projectRoot "tools\libimobiledevice"
$downloadDirectory = Join-Path ([IO.Path]::GetTempPath()) (
    "pixelsync-libimobiledevice-" + [Guid]::NewGuid().ToString("N")
)
$archivePath = Join-Path $downloadDirectory $assetName
$downloadUrl = (
    "https://github.com/jrjr/libimobiledevice-windows/" +
    "releases/download/$releaseTag/$assetName"
)

New-Item -ItemType Directory -Path $downloadDirectory | Out-Null

try {
    Write-Host "Downloading checksum-pinned iPhone tools..."

    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath

    $actualHash = (
        Get-FileHash -LiteralPath $archivePath -Algorithm SHA256
    ).Hash

    if ($actualHash -ne $expectedHash) {
        throw (
            "Checksum mismatch. Expected $expectedHash but received " +
            "$actualHash. No tools were installed."
        )
    }

    New-Item -ItemType Directory -Force -Path $toolDirectory | Out-Null

    Expand-Archive `
        -LiteralPath $archivePath `
        -DestinationPath $toolDirectory `
        -Force

    $requiredFiles = @(
        "idevice_id.exe",
        "ideviceinfo.exe",
        "afcclient.exe",
        "libimobiledevice-1.0.dll"
    )

    foreach ($requiredFile in $requiredFiles) {
        $requiredPath = Join-Path $toolDirectory $requiredFile

        if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
            throw "The archive did not contain $requiredFile."
        }
    }

    Write-Host "iPhone tools installed in $toolDirectory"
}
finally {
    if (Test-Path -LiteralPath $downloadDirectory) {
        Remove-Item -LiteralPath $downloadDirectory -Recurse -Force
    }
}
