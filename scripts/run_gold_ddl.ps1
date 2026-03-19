# Run Gold DDL + backfill in BigQuery (PowerShell). Requires bq CLI and project ethioware-etl.
$ErrorActionPreference = "Stop"
$project = "ethioware-etl"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir

# Step 1: Create tables (DDL)
$ddl_files = @(
    "bq/sql/gold/ddl_dim_date.sql",
    "bq/sql/gold/ddl_dim_learner.sql",
    "bq/sql/gold/ddl_dim_cohort.sql",
    "bq/sql/gold/ddl_dim_field.sql",
    "bq/sql/gold/ddl_dim_institution.sql",
    "bq/sql/gold/ddl_dim_provider.sql",
    "bq/sql/gold/ddl_bridge_learner_field.sql"
)

Push-Location $root
foreach ($f in $ddl_files) {
    $path = Join-Path $root $f
    if (-not (Test-Path $path)) { Write-Warning "Skip (not found): $path"; continue }
    Write-Host "Running $f ..."
    Get-Content $path -Raw | bq query --use_legacy_sql=false --project_id=$project
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
}
Write-Host "DDL complete. Tables created/verified."
Write-Host ""

# Step 2: Backfill dimensions from Silver
Write-Host "Running backfill_dimensions.sql (7 MERGE statements) ..."
$backfill = Join-Path $root "bq/sql/gold/backfill_dimensions.sql"
if (Test-Path $backfill) {
    $sql = Get-Content $backfill -Raw
    # Split on statement separator (double newline before -- ═══) and run each MERGE individually
    $statements = $sql -split '(?=-- ═{5,})' | Where-Object { $_.Trim() -ne "" }
    $i = 0
    foreach ($stmt in $statements) {
        # Extract only the SQL (skip comment-only blocks)
        if ($stmt -match 'MERGE|INSERT') {
            $i++
            Write-Host "  Backfill statement $i ..."
            $stmt | bq query --use_legacy_sql=false --project_id=$project
            if ($LASTEXITCODE -ne 0) { Write-Warning "Statement $i failed"; Pop-Location; exit $LASTEXITCODE }
        }
    }
    Write-Host "Backfill complete ($i statements)."
} else {
    Write-Warning "backfill_dimensions.sql not found at $backfill"
}
Pop-Location
Write-Host "Done."
