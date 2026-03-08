# Run Silver DDL in BigQuery (PowerShell). Requires bq CLI and project ethioware-etl.
$ErrorActionPreference = "Stop"
$project = "ethioware-etl"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir
$files = @(
    "bq/sql/silver/ddl_audit.sql",
    "bq/sql/silver/ddl_rejects.sql",
    "bq/sql/silver/ddl_scores_raw.sql"
)
Push-Location $root
foreach ($f in $files) {
    $path = Join-Path $root $f
    if (-not (Test-Path $path)) { Write-Warning "Skip (not found): $path"; continue }
    Write-Host "Running $f ..."
    Get-Content $path -Raw | bq query --use_legacy_sql=false --project_id=$project
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
}
Pop-Location
Write-Host "Done. Tables: pipeline_run_log, *_rejects, scores_raw."
