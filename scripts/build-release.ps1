[CmdletBinding()]
param(
    [switch]$SkipPackageGate,
    [switch]$SkipWheel
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$previousPythonPath = $env:PYTHONPATH
$sourcePath = Join-Path $repositoryRoot 'src'
$env:PYTHONPATH = if ($previousPythonPath) { "$sourcePath;$previousPythonPath" } else { $sourcePath }

Push-Location $repositoryRoot
try {
    $version = (& python -c "from nvt_combiner.version import __version__; print(__version__)").Trim()
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to read nvt_combiner release version.'
    }
    if ($version -notmatch '^(\d+)\.(\d+)\.(\d+)\.(\d+)$') {
        throw "Release version '$version' must use MAJOR.MINOR.PATCH.BUILD format."
    }

    $windowsVersion = $version
    $versionTuple = "$($matches[1]), $($matches[2]), $($matches[3]), $($matches[4])"
    $releaseDirectory = Join-Path $repositoryRoot 'artifacts\release'
    $versionFile = Join-Path $releaseDirectory 'combiner-version-info.txt'

    & python -m unittest discover -s tests\unit -v
    if ($LASTEXITCODE -ne 0) {
        throw "Unit-test gate failed with exit code $LASTEXITCODE."
    }

    & python -m unittest discover -s tests\module -v
    if ($LASTEXITCODE -ne 0) {
        throw "Module-test gate failed with exit code $LASTEXITCODE."
    }

    New-Item -ItemType Directory -Force -Path $releaseDirectory | Out-Null

    @"
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($versionTuple),
    prodvers=($versionTuple),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Novatek'),
        StringStruct('FileDescription', 'Compatibility-first firmware Combiner'),
        StringStruct('FileVersion', '$windowsVersion'),
        StringStruct('InternalName', 'Combiner'),
        StringStruct('OriginalFilename', 'Combiner.exe'),
        StringStruct('ProductName', 'nvt_combiner'),
        StringStruct('ProductVersion', '$windowsVersion'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@ | Set-Content -LiteralPath $versionFile -Encoding utf8

    & pyinstaller --clean --noconfirm --onefile --name Combiner --paths src `
        --version-file $versionFile `
        --distpath artifacts\pyinstaller\dist --workpath artifacts\pyinstaller\work `
        --specpath artifacts\pyinstaller\spec src\nvt_combiner\__main__.py
    if ($LASTEXITCODE -ne 0) {
        throw 'PyInstaller build failed.'
    }

    $executable = (Resolve-Path artifacts\pyinstaller\dist\Combiner.exe).Path
    $executableVersion = (Get-Item -LiteralPath $executable).VersionInfo
    if (
        $executableVersion.FileVersion -ne $windowsVersion -or
        $executableVersion.ProductVersion -ne $windowsVersion
    ) {
        throw (
            "Windows version resource mismatch. Expected $windowsVersion; " +
            "FileVersion=$($executableVersion.FileVersion); " +
            "ProductVersion=$($executableVersion.ProductVersion)."
        )
    }

    if (-not $SkipPackageGate) {
        $env:COMBINER_EXE = $executable
        & python -m unittest discover -s tests\packaged -v
        if ($LASTEXITCODE -ne 0) {
            throw 'Packaged differential gate failed.'
        }
    }

    if (-not $SkipWheel) {
        & python -m pip wheel --no-deps --wheel-dir artifacts\package-check .
        if ($LASTEXITCODE -ne 0) {
            throw 'Wheel build failed.'
        }
    }

    Get-FileHash $executable -Algorithm SHA256 | Format-List
}
finally {
    if ($null -eq $previousPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $previousPythonPath
    }
    Pop-Location
}
