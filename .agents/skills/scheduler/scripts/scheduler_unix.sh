#!/bin/bash
# Scheduler Setup Script for Linux/Mac (cron)
#
# Creates cron jobs for AI Employee operations:
# - Daily briefing at 8:00 AM
# - Weekly audit on Sunday at 10:00 PM
# - Monthly subscription audit on 1st of each month
#
# Usage:
#   bash scheduler_unix.sh setup
#   bash scheduler_unix.sh list
#   bash scheduler_unix.sh remove

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PYTHON_CMD="python3"
ORCHESTRATOR="$PROJECT_DIR/src/orchestrator.py"
VAULT_PATH="$PROJECT_DIR/AI_Employee_Vault"

# Get absolute paths
PYTHON_PATH=$(which $PYTHON_CMD)
ORCHESTRATOR_PATH=$(realpath $ORCHESTRATOR)
VAULT=$(realpath $VAULT_PATH)

setup_cron_jobs() {
    echo "Setting up cron jobs for AI Employee..."
    echo ""
    
    # Create temporary file for new crontab entries
    TEMP_CRON=$(mktemp)
    
    # Add AI Employee cron jobs
    cat >> "$TEMP_CRON" << EOF
# AI Employee Scheduled Tasks
# Daily briefing at 8:00 AM
0 8 * * * cd $PROJECT_DIR && $PYTHON_PATH $ORCHESTRATOR_PATH $VAULT --scheduled-task daily_briefing >> $PROJECT_DIR/logs/cron_daily_briefing.log 2>&1

# Weekly audit on Sunday at 10:00 PM
0 22 * * 0 cd $PROJECT_DIR && $PYTHON_PATH $ORCHESTRATOR_PATH $VAULT --scheduled-task weekly_audit >> $PROJECT_DIR/logs/cron_weekly_audit.log 2>&1

# Monthly subscription audit on 1st of month at 9:00 AM
0 9 1 * * cd $PROJECT_DIR && $PYTHON_PATH $ORCHESTRATOR_PATH $VAULT --scheduled-task subscription_audit >> $PROJECT_DIR/logs/cron_monthly_audit.log 2>&1
EOF

    # Install crontab
    # Backup existing crontab first
    crontab -l > /tmp/cron_backup_$$ 2>/dev/null || true
    
    # Combine existing and new entries
    if [ -s /tmp/cron_backup_$$ ]; then
        cat /tmp/cron_backup_$$ "$TEMP_CRON" | crontab -
    else
        cat "$TEMP_CRON" | crontab -
    fi
    
    # Cleanup
    rm -f "$TEMP_CRON" /tmp/cron_backup_$$
    
    echo "✓ Cron jobs installed!"
    echo ""
    echo "To verify, run: crontab -l"
    echo "To view logs: tail -f $PROJECT_DIR/logs/cron_*.log"
}

list_cron_jobs() {
    echo "Current crontab entries for AI Employee:"
    echo ""
    crontab -l 2>/dev/null | grep -E "(AI Employee|daily_briefing|weekly_audit|subscription_audit)" || echo "No AI Employee cron jobs found"
}

remove_cron_jobs() {
    echo "Removing AI Employee cron jobs..."
    echo ""
    
    # Get current crontab and filter out AI Employee entries
    crontab -l 2>/dev/null | grep -v -E "(AI Employee|daily_briefing|weekly_audit|subscription_audit)" | crontab -
    
    echo "✓ AI Employee cron jobs removed!"
    echo ""
    echo "To verify, run: crontab -l"
}

# Main entry point
case "${1,,}" in
    setup)
        setup_cron_jobs
        ;;
    list)
        list_cron_jobs
        ;;
    remove)
        remove_cron_jobs
        ;;
    *)
        echo "Usage: bash scheduler_unix.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup   - Install cron jobs"
        echo "  list    - List cron jobs"
        echo "  remove  - Remove cron jobs"
        exit 1
        ;;
esac
