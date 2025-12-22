# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered goal-setting system based on scientifically validated methods. The system helps users formulate goals, break them down into a three-level structure (Strategy → Tactics → Operations), generate reflections, and track progress through automated Python scripts.

## Core Architecture: Three-Level System

The system is built around a **mandatory three-level hierarchy** for every goal:

### Level 1: STRATEGY (Identity-Based Goals)
- **Horizon:** 1-5 years
- **Focus:** Desired identity, beliefs, principles
- **Format:** "I am [description], who [action/principle]"
- **Method:** Identity-Based Motivation

### Level 2: TACTICS (OKR or SMART)
- **Horizon:** 3-12 months
- **Focus:** Measurable goals, progress metrics
- **Format:** Objective + Key Results (for OKR) or SMART goal
- **Methods:** OKR (medium-term) or SMART (short-term)

### Level 3: OPERATIONS (Implementation Intentions + Tiny Habits)
- **Horizon:** Daily
- **Focus:** Specific actions, triggers, habits
- **Format:** If-Then plans and Tiny Habits with anchors
- **Methods:** If-Then planning, Tiny Habits

**CRITICAL:** All three levels must always be present and clearly separated. Never mix levels.

## Common Commands

### Daily Workflow

```bash
# Generate daily reflection template (morning)
python3 scripts/generate_reflection.py

# Analyze filled reflection (evening, or ask AI coach: "Analyze today's reflection")
# The AI coach will read, analyze, and update the reflection file automatically

# Update goal metrics from reflection data
python3 scripts/auto_update_metrics.py

# Track habit streaks
python3 scripts/track_habit_streaks.py

# Generate daily dashboard (HTML + Markdown)
python3 scripts/generate_daily_dashboard.py

# Open today's dashboard
open dashboards/daily/$(date +%Y-%m-%d).html
```

### Weekly Workflow

```bash
# Generate weekly dashboard
python3 scripts/generate_weekly_dashboard.py

# Validate goals structure
python3 scripts/validate_goals.py

# Auto-fix validation issues
python3 scripts/validate_goals.py --fix
```

### Automation Management

```bash
# Setup cron schedule for automation
python3 scripts/schedule_manager.py setup

# Check automation status
python3 scripts/schedule_manager.py status

# Enable/disable automation
python3 scripts/schedule_manager.py enable
python3 scripts/schedule_manager.py disable

# Run entire daily pipeline manually (for testing)
python3 scripts/schedule_manager.py run daily

# Run individual tasks
python3 scripts/schedule_manager.py run analyze_reflection
python3 scripts/schedule_manager.py run daily_dashboard
```

### Testing Individual Scripts

```bash
# Generate reflection for specific date
python3 scripts/generate_reflection.py --date 2025-12-21

# Update metrics for specific period
python3 scripts/auto_update_metrics.py --date 2025-12-21
python3 scripts/auto_update_metrics.py --period week

# Generate dashboard for specific date
python3 scripts/generate_daily_dashboard.py --date 2025-12-21
```

## Goal Change Tracking System

When updating goals, changes MUST be classified into one of four types:

1. **`[PROGRESS]`** - Natural progress, metric updates
   - Example: Updating KR progress from 45% to 50%

2. **`[FORCED_CHANGE]`** - Forced changes due to crisis/emergency
   - Example: Lost job, accident, illness, force majeure
   - **MUST be added to "КРИТИЧЕСКИЕ СОБЫТИЯ" section**

3. **`[VOLUNTARY_CHANGE]`** - Voluntary changes from reflection
   - Example: Changed priorities, new understanding, pivot

4. **`[PLAN_ADJUSTMENT]`** - Tactical/operational plan adjustments
   - Example: Changed If-Then triggers, adjusted KR metrics

See `prompts/goal_change_tracking.md` for detailed classification logic.

## Directory Structure & Data Format

### Goals
- Path: `goals/goal_YYYY_MM_DD_[description].md`
- Each goal contains all three levels + change history
- Status: `active`, `paused`, `completed`, `cancelled`

### Reflections
```
reflections/
├── daily/YYYY/MM/YYYY-MM-DD.md
├── weekly/YYYY/week_NN_YYYY.md
├── monthly/YYYY/YYYY-MM.md
├── quarterly/YYYY/QN_YYYY.md
└── yearly/YYYY.md
```

### Dashboards
```
dashboards/
├── daily/YYYY-MM-DD.{html,md}
├── weekly/week_NN_YYYY.{html,md}
├── streaks/YYYY-MM-DD_streaks.md
└── validation/YYYY-MM-DD_validation_report.md
```

### Configuration Files
- `config/schedule.yaml` - Cron automation schedule
- `config/notifications.yaml` - Notification settings (macOS, Telegram, Slack)
- `config/git_auto_commit.yaml` - Git auto-commit configuration

## AI Coach Workflow

When working with the AI coach (as defined in `.cursorrules`):

### Creating a New Goal
1. User states their goal
2. AI uses prompts in sequence:
   - `prompts/goal_formulation.md` - Formulate the goal
   - `prompts/strategy_level.md` - Create strategic level
   - `prompts/tactics_level.md` - Create tactical level
   - `prompts/operations_level.md` - Create operational level
   - `prompts/checklist_creation.md` - Create tracking checklists
3. AI saves goal to `goals/` using `prompts/goal_management.md`

### Daily Reflection Analysis
1. User fills out reflection template
2. User tells AI: "Analyze today's reflection" (or similar)
3. AI:
   - Reads reflection file from `reflections/daily/YYYY/MM/YYYY-MM-DD.md`
   - Analyzes operation execution, tactics progress, identity evidence
   - Detects critical events (using `prompts/goal_change_tracking.md`)
   - Generates "Комментарии ИИ-системы" section with analysis
   - Updates reflection file with comments
   - Updates goal files if needed (metrics, critical events)

### Progress Tracking
- Use `prompts/progress_tracking.md` for analyzing progress
- Always update "Последнее обновление" and "ИСТОРИЯ ИЗМЕНЕНИЙ" in goal files
- Use `prompts/reflection_management.md` for reflection analysis details

## Automated Pipeline (Cron)

### Daily Pipeline (21:00-21:25)
```
21:00 - analyze_reflection    # Analyze filled daily reflection
21:05 - update_metrics         # Update goal metrics from reflection
21:10 - track_streaks          # Track habit streaks
21:15 - daily_dashboard        # Generate HTML dashboard
21:20 - git_commit             # Auto-commit changes
21:25 - notify_daily           # Send notification
```

### Weekly Pipeline (Sunday 22:00)
```
22:00 - weekly_dashboard       # Generate weekly analytics
22:05 - validate_structure     # Validate goals structure
22:10 - notify_weekly          # Send weekly notification
```

### Health Checks (Hourly)
- Check for unfilled reflections (after 12:00)
- Warn if streak is at risk (<3 days)
- Alert on low performance patterns

## Scientific Methods Reference

The system implements evidence-based goal-setting methods from `goal_setting_guide.md`:

- **SMART Goals:** Doran (1981), Locke & Latham (2002)
- **OKR:** Objectives and Key Results framework
- **WOOP:** Oettingen (2014) - Wish, Outcome, Obstacle, Plan
- **Implementation Intentions:** Gollwitzer (1999) - If-Then planning
- **Identity-Based Motivation:** Oyserman (2007, 2015)
- **Tiny Habits:** Fogg (2019), Lally et al. (2010)
- **Self-Determination Theory:** Deci & Ryan (1985, 2000)

## Important Constraints from .cursorrules

1. **Always use three levels** - Strategy, Tactics, Operations must be clearly separated
2. **Always use prompts** - Each stage has a corresponding prompt in `prompts/`
3. **Track all changes** - Update "ИСТОРИЯ ИЗМЕНЕНИЙ" with proper type tags
4. **Critical events** - FORCED_CHANGE events go to "КРИТИЧЕСКИЕ СОБЫТИЯ" section
5. **Never skip steps** - Follow the sequential workflow defined in rules
6. **Use scientific methods only** - All methods must be from `goal_setting_guide.md`

## Script Architecture

### Key Scripts
- `generate_reflection.py` - Parses active goals, generates reflection templates
- `analyze_reflection.py` - Detects critical events, analyzes progress (or use AI coach)
- `auto_update_metrics.py` - Updates KR progress, evidence counts, streaks
- `track_habit_streaks.py` - Calculates current/max streaks, patterns by weekday
- `generate_daily_dashboard.py` - Creates HTML/SVG visualizations
- `schedule_manager.py` - Central cron management (setup, enable, disable, run)
- `notification_system.py` - Multi-channel notifications (macOS, Telegram, Slack)
- `validate_goals.py` - Structure validation with auto-fix capability

### Common Patterns
All scripts follow:
- Use `PROJECT_ROOT = Path(__file__).parent.parent`
- Parse goal files with regex to extract structured data
- Log to `logs/` directory with timestamps
- Return exit code 0 (success) or 1 (error)
- Support `--date` parameter for historical processing

## Git Auto-Commit Templates

Commits are automatically created with these templates:
- `📝 Daily reflection: {date}`
- `📊 Daily dashboard: {date}`
- `📈 Weekly dashboard: week {week} {year}`
- `🎯 Goals update: metrics auto-update`
- `✅ Validation: structure fix`

**Note:** `auto_push` is disabled by default for safety. Enable only for private repos.

## Notification Channels

Configure in `config/notifications.yaml`:

1. **macOS Notification Center** (built-in)
   - Requires Terminal notification permissions
   - Uses osascript for native notifications

2. **Telegram** (optional)
   - Create bot via @BotFather
   - Get chat_id from @userinfobot
   - Requires `pip3 install requests`

3. **Slack** (optional)
   - Create Incoming Webhook
   - Requires `pip3 install requests`

## Troubleshooting

- **Scripts fail:** Check `logs/cron/` for detailed error messages
- **Cron not running:** Verify with `python3 scripts/schedule_manager.py status`
- **Validation errors:** Run `python3 scripts/validate_goals.py` to see issues
- **Reflection not analyzed:** Ensure file exists in correct location: `reflections/daily/YYYY/MM/YYYY-MM-DD.md`

For detailed troubleshooting, see `docs/TROUBLESHOOTING.md`.

## Key Files to Reference

- `.cursorrules` - Complete AI coach behavior rules
- `goal_setting_guide.md` - Scientific foundation and method descriptions
- `DATA_STRUCTURE.md` - Detailed data structure documentation
- `docs/SCRIPTS.md` - Comprehensive script documentation
- `docs/AUTOMATION.md` - Automation setup and management guide
- `prompts/*.md` - Individual prompts for each workflow stage
