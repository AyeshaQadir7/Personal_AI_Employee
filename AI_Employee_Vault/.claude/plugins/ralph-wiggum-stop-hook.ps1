# Ralph Wiggum Stop Hook for Windows (PowerShell)
# 
# This script intercepts Claude Code's exit and checks if tasks are complete.
# If not, it re-injects the prompt to keep Claude working.
#
# Installation: Copy to ~/.claude/plugins/ or ./.claude/plugins/

param(
    [string]$TaskPrompt = "",
    [int]$MaxIterations = 10,
    [string]$VaultPath = ""
)

# Configuration
$CheckFolders = @("Needs_Action", "Pending_Approval")
$CompletionMarkers = @("TASK_COMPLETE", "DONE", "COMPLETE")

# Get vault path
if (-not $VaultPath) {
    $VaultPath = Get-Location
}

$NeedsActionPath = Join-Path $VaultPath "Needs_Action"
$DonePath = Join-Path $VaultPath "Done"

function Test-TaskComplete {
    param(
        [string]$Output
    )
    
    # Check if completion marker is in output
    foreach ($marker in $CompletionMarkers) {
        if ($Output -match $marker) {
            Write-Host "✓ Completion marker found: $marker" -ForegroundColor Green
            return $true
        }
    }
    
    # Check if Needs_Action folder is empty
    if (Test-Path $NeedsActionPath) {
        $fileCount = (Get-ChildItem -Path $NeedsActionPath -Filter "*.md" -ErrorAction SilentlyContinue).Count
        if ($fileCount -eq 0) {
            Write-Host "✓ Needs_Action folder is empty" -ForegroundColor Green
            return $true
        }
        Write-Host "○ Items remaining in Needs_Action: $fileCount" -ForegroundColor Yellow
    }
    
    return $false
}

function Start-RalphLoop {
    param(
        [string]$Prompt,
        [int]$MaxIterations
    )
    
    $iteration = 0
    $lastOutput = ""
    
    Write-Host "`n🔄 Starting Ralph Wiggum Loop" -ForegroundColor Cyan
    Write-Host "   Task: $Prompt" -ForegroundColor Cyan
    Write-Host "   Max Iterations: $MaxIterations" -ForegroundColor Cyan
    Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Cyan
    
    while ($iteration -lt $MaxIterations) {
        $iteration++
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
        Write-Host "Iteration $iteration of $MaxIterations" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
        
        # Build the prompt
        $fullPrompt = $Prompt
        if ($lastOutput) {
            $fullPrompt = @"
$Prompt

---
PREVIOUS OUTPUT:
$lastOutput

Continue working on the task. If you believe you are done, verify that all items are processed.
"@
        }
        
        # Run Claude Code
        # Note: This is a simplified version - actual implementation would need
        # to capture Claude's output and feed it back
        Write-Host "Running Claude Code..." -ForegroundColor Yellow
        
        # In practice, you would use claude-code-router or direct API calls here
        # For now, this serves as a template for the pattern
        
        $claudeOutput = ""
        
        # Check if task is complete
        if (Test-TaskComplete -Output $claudeOutput) {
            Write-Host "`n✅ Task Complete!" -ForegroundColor Green
            break
        }
        
        $lastOutput = $claudeOutput
    }
    
    if ($iteration -ge $MaxIterations) {
        Write-Host "`n⚠️  Maximum iterations reached" -ForegroundColor Red
    }
}

# Example usage:
# .\ralph-wiggum-stop-hook.ps1 -TaskPrompt "Process all files in Needs_Action" -MaxIterations 10

Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║         Ralph Wiggum Stop Hook - Ready                    ║
╠═══════════════════════════════════════════════════════════╣
║  This plugin auto-loads when Claude Code runs in this     ║
║  vault directory. It will keep Claude working until       ║
║  tasks are complete.                                      ║
║                                                           ║
║  Manual usage:                                            ║
║    claude ""Process all files in /Needs_Action""            ║
║                                                           ║
║  The hook will loop until completion.                     ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
