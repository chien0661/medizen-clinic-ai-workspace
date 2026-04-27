# Telegram Release Notification Setup

**Purpose**: Automatically send release notifications to Telegram channel/group when a new version is released.

**Audience**: Template Maintainers Only

---

## Quick Setup (5 minutes)

### Step 1: Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to name your bot:
   - **Bot name**: `AI Team Template Release Bot` (or your choice)
   - **Bot username**: `ai_team_template_bot` (must end with 'bot')
4. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Save this token securely

### Step 2: Get Chat ID

**Option A: For Channel**
1. Create a Telegram channel (if not exists)
2. Add your bot as an administrator to the channel
3. Get channel username (e.g., `@ai_team_releases`)
4. Chat ID = `@ai_team_releases`

**Option B: For Private Group**
1. Create a Telegram group (if not exists)
2. Add your bot to the group
3. Send a message to the group
4. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Look for `"chat":{"id":-123456789,...}`
6. Chat ID = `-123456789` (negative number for groups)

**Option C: Use IDBot**
1. Add `@myidbot` to your channel/group
2. Send `/getid` command
3. Copy the Chat ID

### Step 3: Set Environment Variables

**For Windows PowerShell (Persistent):**
```powershell
[System.Environment]::SetEnvironmentVariable('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN', 'User')
[System.Environment]::SetEnvironmentVariable('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID', 'User')
[System.Environment]::SetEnvironmentVariable('REPO_URL', 'https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team', 'User')
```

**For Linux/macOS (Add to ~/.bashrc or ~/.zshrc):**
```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
export REPO_URL="https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team"
```

**Temporary (Current Session Only):**
```bash
# Windows (PowerShell)
$env:TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
$env:TELEGRAM_CHAT_ID="YOUR_CHAT_ID"

# Linux/macOS
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

### Step 4: Test the Notification

```bash
# Navigate to template repository
cd template-ai-team

# Run notification script
node scripts/send-release-notification.js
```

**Expected output:**
```
🚀 Starting release notification...

📊 Gathering release information...
   Version: 1.2.2-RELEASE
   Type: PATCH
   Date: 2026-01-27
   Commits: 2

📝 Reading CHANGELOG.md...

📤 Formatting Telegram message...

📨 Sending to Telegram...
✅ Release notification sent successfully!
   Message ID: 123
   Chat ID: -987654321
   Chat Title: AI Team Releases

✨ Done!
```

---

## How It Works

### 1. **Automatic Information Gathering**
The script automatically extracts:
- ✅ Latest git tag (version)
- ✅ Release type (PATCH/MINOR/MAJOR)
- ✅ Release date
- ✅ Commit count since previous release
- ✅ Commit hash
- ✅ Tag message
- ✅ Changelog entries from CHANGELOG.md

### 2. **Formatted Telegram Message**
Example message sent to Telegram:

```
🔧 AI Team Template 1.2.2-RELEASE

📅 Release Date: 2026-01-27
🏷️ Type: PATCH
📝 Commits: 2 commits
🔗 Commit: b913109

Version 1.2.2 - Enhanced project-setup skill

What's New:
### Enhanced
#### /project-setup Skill - Improved Existing Project Workflow
- Enhanced /project-setup command for better existing project integration
- NEW: Prompts user to input full path to existing project directory
- NEW: Automatically navigates to provided directory
[... more entries ...]

🔗 View Release
📖 Full Changelog

Released by AI Team Template Maintainers
```

### 3. **Emoji Icons by Release Type**
- 🚀 **MAJOR** - Breaking changes (X.0.0)
- ✨ **MINOR** - New features (1.X.0)
- 🔧 **PATCH** - Bug fixes (1.2.X)

---

## Integration with Release Process

### Add to Your Release Workflow

After pushing to remote, run the notification script:

```bash
# Complete release process
git push origin master
git push origin X.X.X-RELEASE

# Send release notification
node scripts/send-release-notification.js
```

**Recommended**: Add this to `docs/RELEASE_PROCESS.md` as the final step.

---

## Troubleshooting

### Issue: "TELEGRAM_BOT_TOKEN environment variable is required"

**Solution**: Set the environment variable
```bash
# Check if variable is set
echo $TELEGRAM_BOT_TOKEN  # Linux/macOS
echo $env:TELEGRAM_BOT_TOKEN  # Windows PowerShell

# If empty, set it
export TELEGRAM_BOT_TOKEN="your-token-here"
```

### Issue: "Telegram API error: 400 - Bad Request"

**Possible causes:**
1. **Invalid Chat ID** - Check chat ID is correct
2. **Bot not added to channel/group** - Add bot as admin
3. **Invalid markdown** - The script escapes markdown, but check for issues

**Solution**:
```bash
# Test bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# Test sending simple message
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/sendMessage \
  -d chat_id=<CHAT_ID> \
  -d text="Test message"
```

### Issue: "Error getting release info: Command failed"

**Solution**: Ensure you're in a git repository with tags
```bash
# Check git repository
git status

# Check tags exist
git tag -l

# Ensure latest commit is tagged
git describe --tags
```

### Issue: "Changelog unavailable"

**Solution**: Ensure CHANGELOG.md exists and is properly formatted
```bash
# Check file exists
ls -la CHANGELOG.md

# Verify format (should have ## [X.X.X] - YYYY-MM-DD)
head -30 CHANGELOG.md
```

### Issue: Bot can't send to private group

**Solution**: Ensure bot has correct permissions
1. Add bot to group as admin
2. Grant "Post Messages" permission
3. Try sending test message
4. Check bot status: `@BotFather` → `/mybots` → Select bot → Bot Settings

---

## Configuration Options

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | Telegram bot token from @BotFather | `123456789:ABCdef...` |
| `TELEGRAM_CHAT_ID` | ✅ Yes | Channel/group chat ID | `@channel` or `-123456789` |
| `REPO_URL` | ⚠️ Optional | Repository URL for links | `https://bitbucket.vissoft.vn/...` |
| `RELEASE_VERSION` | ⚠️ Optional | Override version detection | `1.2.2-RELEASE` |
| `RELEASE_TYPE` | ⚠️ Optional | Override release type | `PATCH` |

### Script Arguments

Currently no command-line arguments. All configuration via environment variables.

---

## Security Best Practices

### ✅ DO:
- Store tokens in environment variables (never in code)
- Use separate bots for different projects
- Limit bot permissions to minimum required
- Keep bot token secret (don't share publicly)
- Use private groups for internal releases
- Rotate tokens periodically

### ❌ DON'T:
- Commit tokens to Git
- Share bot tokens in chat/email
- Use admin accounts as bots
- Grant unnecessary permissions
- Post sensitive info in public channels

---

## Advanced Usage

### Custom Message Format

Edit `scripts/send-release-notification.js` to customize:
- Emoji icons (line ~77)
- Message template (line ~89-109)
- Changelog preview length (line ~105)

### Multiple Channels

To send to multiple channels, run script multiple times with different `TELEGRAM_CHAT_ID`:

```bash
# Channel 1: Public announcements
TELEGRAM_CHAT_ID="@public_releases" node scripts/send-release-notification.js

# Channel 2: Internal team
TELEGRAM_CHAT_ID="-123456789" node scripts/send-release-notification.js
```

### CI/CD Integration

Add to your CI/CD pipeline (GitHub Actions, GitLab CI, etc.):

**GitHub Actions example:**
```yaml
- name: Send Telegram Notification
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: node scripts/send-release-notification.js
```

---

## Example Notifications

### PATCH Release (1.2.2)
```
🔧 AI Team Template 1.2.2-RELEASE

📅 Release Date: 2026-01-27
🏷️ Type: PATCH
📝 Commits: 2 commits
🔗 Commit: b913109

Version 1.2.2 - Enhanced project-setup skill

What's New:
### Enhanced
- Enhanced /project-setup command...
```

### MINOR Release (1.3.0)
```
✨ AI Team Template 1.3.0-RELEASE

📅 Release Date: 2026-02-15
🏷️ Type: MINOR
📝 Commits: 15 commits
🔗 Commit: abc1234

Version 1.3.0 - New AI agents and features

What's New:
### Added
- New Security Agent for automated audits
- New /security-scan command...
```

### MAJOR Release (2.0.0)
```
🚀 AI Team Template 2.0.0-RELEASE

📅 Release Date: 2026-06-01
🏷️ Type: MAJOR
📝 Commits: 50 commits
🔗 Commit: def5678

Version 2.0.0 - Complete architecture redesign

⚠️ BREAKING CHANGES
- New workflow structure requires migration
- Updated agent configurations...
```

---

## FAQ

**Q: Can I send to multiple channels?**
A: Yes, run the script multiple times with different `TELEGRAM_CHAT_ID` values.

**Q: Can I customize the message format?**
A: Yes, edit `scripts/send-release-notification.js` and modify the `formatTelegramMessage()` function.

**Q: Does it work with Telegram Desktop/Web?**
A: Yes, it works with all Telegram clients (mobile, desktop, web).

**Q: Can I send to private chat?**
A: Yes, use your personal chat ID instead of channel/group ID.

**Q: Is this required for releases?**
A: No, it's optional. But highly recommended for team communication.

**Q: What if CHANGELOG.md is not found?**
A: The script will still work, but show "Changelog unavailable" instead of entries.

---

## Related Documentation

- **[RELEASE_PROCESS.md](RELEASE_PROCESS.md)** - Complete release process guide
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history
- **[README.md](../README.md)** - Project overview

---

**Last Updated**: 2026-01-27
**Script Version**: 1.0.0
**Audience**: Template Maintainers Only
