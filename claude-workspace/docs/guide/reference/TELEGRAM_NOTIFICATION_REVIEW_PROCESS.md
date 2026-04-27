# Telegram Notification Review Process

**Purpose**: Prevent notification mistakes by requiring review before sending to team channel.

---

## Overview

All release notifications now use a **two-step review process**:

1. **Preview** - Send to private chat for review
2. **Send** - Send to team channel after approval

This prevents mistakes like:
- Missing important features in notification
- Wrong version information
- Incomplete documentation
- Multiple conflicting notifications

---

## Setup

### 1. Get Your Private Chat ID

Run the helper script to get your Telegram private chat ID:

```bash
node scripts/get-my-chat-id.js
```

**Instructions:**
1. Run the script
2. Open Telegram
3. Find the bot: `@VissoftAITeamBot`
4. Send any message to the bot (e.g., "hello")
5. The script will display your chat ID

**Example output:**
```
👤 Private Chat Found:
   Name: Quang Vinh
   Username: @quangvinh
   Chat ID: 123456789
   Last message: "hello"

✅ Found your private chat!

📋 Set this as environment variable:
   Windows PowerShell:
   $env:TELEGRAM_PRIVATE_CHAT_ID="123456789"
```

### 2. Set Environment Variable

**Windows PowerShell:**
```powershell
$env:TELEGRAM_PRIVATE_CHAT_ID="your-chat-id"
```

**Linux/macOS:**
```bash
export TELEGRAM_PRIVATE_CHAT_ID="your-chat-id"
```

**Permanent (add to .env file):**
```
TELEGRAM_PRIVATE_CHAT_ID=your-chat-id
```

---

## Usage

### Step 1: Send Preview (Review)

After completing the release (CHANGELOG, README, commit, tag, push), send preview to your private chat:

```bash
node scripts/send-release-notification.js --preview
```

**What happens:**
- Generates the release notification
- Sends to **your private chat only**
- Shows instructions for next steps

**Expected output:**
```
🚀 Starting release notification (PREVIEW MODE)...

📊 Gathering release information...
   Version: 1.5.0-RELEASE
   Type: MINOR
   Date: 2026-02-03
   Commits: 12

📝 Reading CHANGELOG.md...

📤 Formatting Telegram message...

📨 Sending private chat for review...
✅ Preview sent to private chat!
   Message ID: 42
   Chat: Quang Vinh

⏸️  WAITING FOR YOUR REVIEW

   Please check the message in your private chat.

   If everything looks correct:
     ✅ Run: node scripts/send-release-notification.js --send

   If you need to fix something:
     ❌ Fix the issue, then re-run with --preview

✨ Done!
```

### Step 2: Review in Private Chat

Open Telegram and check your private chat with the bot. Review the notification message:

**Check:**
- ✅ Version number is correct
- ✅ Release type is correct (MAJOR/MINOR/PATCH)
- ✅ Date is correct
- ✅ All major features are included
- ✅ CHANGELOG content is accurate
- ✅ Links work correctly
- ✅ Formatting looks good
- ✅ No typos or errors

**If issues found:**
1. Fix the issue (update CHANGELOG, README, etc.)
2. Re-run preview: `node scripts/send-release-notification.js --preview`
3. Review again

**If everything correct:**
- Proceed to Step 3

### Step 3: Send to Team Channel (After Approval)

Once you've confirmed the preview is correct, send to team channel:

```bash
node scripts/send-release-notification.js --send
```

**What happens:**
- Sends the **exact same message** to team channel
- Confirms successful delivery

**Expected output:**
```
🚀 Starting release notification (TEAM CHANNEL)...

📊 Gathering release information...
   Version: 1.5.0-RELEASE
   Type: MINOR
   Date: 2026-02-03
   Commits: 12

📝 Reading CHANGELOG.md...

📤 Formatting Telegram message...

📨 Sending TEAM CHANNEL...
✅ Release notification sent successfully!
   Message ID: 28
   Chat ID: -5194367684
   Chat Title: VISSOFT Claude Code

✨ Done!
```

---

## Troubleshooting

### Error: "TELEGRAM_PRIVATE_CHAT_ID environment variable is required"

**Solution:**
```bash
# Get your chat ID
node scripts/get-my-chat-id.js

# Set environment variable
$env:TELEGRAM_PRIVATE_CHAT_ID="your-chat-id"
```

### Error: "No messages found"

**Solution:**
1. Make sure you've sent a message to the bot in a **private chat** (not group)
2. Message the bot directly: `@VissoftAITeamBot`
3. Run the script again: `node scripts/get-my-chat-id.js`

### Preview sent but I can't find it

**Solution:**
- Search for `@VissoftAITeamBot` in Telegram
- Check your direct messages
- The bot should have a message from "AI Team Reporter"

### Need to resend preview after fixing issues

**Solution:**
- Just run `--preview` again
- Delete the old preview message manually if needed
- The new preview will be sent as a new message

---

## Environment Variables Summary

| Variable | Required For | Description |
|----------|--------------|-------------|
| `TELEGRAM_BOT_TOKEN` | Both | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | `--send` | Team channel ID (-5194367684) |
| `TELEGRAM_PRIVATE_CHAT_ID` | `--preview` | Your private chat ID for review |
| `REPO_URL` | Both (optional) | Repository URL (has default) |

---

## Benefits

✅ **Prevents mistakes** - Review before team sees notification
✅ **Catches missing features** - Ensure all changes are documented
✅ **Validates formatting** - See exactly how it looks before sending
✅ **Allows fixes** - Fix issues without confusing the team
✅ **No cleanup needed** - Private chat previews don't clutter team channel

---

## Integration with /release Skill

The `/release` skill automatically uses this two-step process:

**Step 9a: Send preview**
```bash
node scripts/send-release-notification.js --preview
```

**Step 9b: Send to team (after your approval)**
```bash
node scripts/send-release-notification.js --send
```

See [/release skill documentation](./.claude/skills/release/SKILL.md) for complete release workflow.

---

**Last Updated**: 2026-02-03
**Related**: TELEGRAM_NOTIFICATION_SETUP.md, /release skill
