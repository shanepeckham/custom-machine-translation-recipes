param([Parameter(Mandatory=$True)][string]$lp,
      [Parameter(Mandatory=$True)][string]$sha,
      [Parameter(Mandatory=$True)][string]$workspaceId)

$languagePath = $lp.Replace(':', '_')
$docObj = translator document list -ws $workspaceId --json | Out-String | ConvertFrom-Json
$docList = $docObj | Where-Object { $_.name.Contains($languagePath) -and $_.name.Contains($sha) } | Select-Object -ExpandProperty id
$docListcsv = $docList -join ","
echo "::set-env name=DocIds-$lp::$docListcsv"