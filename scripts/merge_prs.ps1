Param(
  [string]$BaseBranch = 'master',
  [int[]]$PrNumbers = @(14,15,16),
  [switch]$Push
)

function Exec($cmd) {
  Write-Host "PS> $cmd" -ForegroundColor Cyan
  $out = Invoke-Expression $cmd
  return $out
}

Exec "git checkout $BaseBranch"
foreach ($n in $PrNumbers) {
  $branch = "pr/$n"
  try {
    Exec "git merge --no-ff -m \"Merge PR #$n into $BaseBranch\" $branch"
    Write-Host "PR #$n uspešno zmergan v $BaseBranch" -ForegroundColor Green
  }
  catch {
    Write-Warning "Konflikt pri PR #$n. Reši konflikte, nato: git add -A; git commit --no-edit"
    break
  }
}

if ($Push) {
  try {
    Exec "git push origin $BaseBranch"
    Write-Host "Push izveden na origin/$BaseBranch" -ForegroundColor Green
  }
  catch {
    Write-Warning "Push ni uspel: $($_.Exception.Message)"
  }
}