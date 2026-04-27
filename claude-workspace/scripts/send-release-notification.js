#!/usr/bin/env node

/**
 * Release Notification Script
 *
 * DO NOT DELETE - Required by /release skill (Step 9: Telegram notification)
 *
 * Two-step process to prevent notification mistakes:
 *   1. Preview: Send to private chat for review
 *   2. Send: Send to team channel after approval
 *
 * Usage:
 *   node scripts/send-release-notification.js --preview   # Step 1: Review
 *   node scripts/send-release-notification.js --send      # Step 2: Send to team
 *
 * Environment Variables Required:
 *   TELEGRAM_BOT_TOKEN - Telegram bot token from @BotFather
 *   TELEGRAM_CHAT_ID - Team channel chat ID
 *   TELEGRAM_PRIVATE_CHAT_ID - Your private chat ID for preview
 *
 * Optional:
 *   RELEASE_VERSION - Override version detection
 *   RELEASE_TYPE - Override release type (PATCH/MINOR/MAJOR)
 *   REPO_URL - Repository URL
 */

const https = require('https');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const isPreviewMode = args.includes('--preview');
const isSendMode = args.includes('--send');

if (!isPreviewMode && !isSendMode) {
  console.error('Usage:');
  console.error('  node scripts/send-release-notification.js --preview   # Send to private chat for review');
  console.error('  node scripts/send-release-notification.js --send      # Send to team channel');
  process.exit(1);
}

if (isPreviewMode && isSendMode) {
  console.error('Error: Cannot use both --preview and --send at the same time');
  process.exit(1);
}

// Configuration
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;
const TELEGRAM_PRIVATE_CHAT_ID = process.env.TELEGRAM_PRIVATE_CHAT_ID;
const REPO_URL = process.env.REPO_URL || 'https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team';

// Validation
if (!TELEGRAM_BOT_TOKEN) {
  console.error('Error: TELEGRAM_BOT_TOKEN environment variable is required');
  process.exit(1);
}

if (isSendMode && !TELEGRAM_CHAT_ID) {
  console.error('Error: TELEGRAM_CHAT_ID environment variable is required for --send mode');
  process.exit(1);
}

if (isPreviewMode && !TELEGRAM_PRIVATE_CHAT_ID) {
  console.error('Error: TELEGRAM_PRIVATE_CHAT_ID environment variable is required for --preview mode');
  process.exit(1);
}

/**
 * Get latest release information from git
 */
function getReleaseInfo() {
  try {
    const latestTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf-8' }).trim();
    const tagMessage = execSync(`git tag -l --format="%(contents)" ${latestTag}`, { encoding: 'utf-8' }).trim();

    // Get commit count since previous tag
    const allTags = execSync('git tag -l "*-RELEASE" --sort=-version:refname', { encoding: 'utf-8' }).trim().split('\n');
    const currentIndex = allTags.indexOf(latestTag);
    const previousTag = currentIndex >= 0 && currentIndex < allTags.length - 1 ? allTags[currentIndex + 1] : '';
    const commitCount = previousTag
      ? execSync(`git rev-list ${previousTag}..${latestTag} --count`, { encoding: 'utf-8' }).trim()
      : '1';

    const commitHash = execSync(`git rev-list -n 1 --abbrev-commit ${latestTag}`, { encoding: 'utf-8' }).trim();
    const releaseDate = execSync(`git log -1 --format=%ai ${latestTag}`, { encoding: 'utf-8' }).trim().split(' ')[0];

    // Determine release type from version number
    const versionMatch = latestTag.match(/(\d+)\.(\d+)\.(\d+)/);
    let releaseType = 'PATCH';
    if (versionMatch) {
      const [_, major, minor, patch] = versionMatch;
      if (patch === '0' && minor === '0') releaseType = 'MAJOR';
      else if (patch === '0') releaseType = 'MINOR';
    }

    return { version: latestTag, message: tagMessage, commitCount, commitHash, releaseDate, releaseType, previousTag };
  } catch (error) {
    console.error('Error getting release info:', error.message);
    process.exit(1);
  }
}

/**
 * Read CHANGELOG.md and extract latest release notes
 */
function getChangelogEntries() {
  try {
    const changelogPath = path.join(__dirname, '..', 'CHANGELOG.md');
    const changelog = fs.readFileSync(changelogPath, 'utf-8');

    const latestTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf-8' }).trim();
    const versionNumber = latestTag.replace(/-PRE-RELEASE$/, '').replace(/-RELEASE$/, '');

    const lines = changelog.split(/^## \[/m);

    for (const section of lines) {
      if (section.startsWith(versionNumber + ']')) {
        const contentLines = section.split(/\r?\n/).slice(1);
        const content = contentLines.join('\n').trim();
        const nextSectionIndex = content.indexOf('\n## [');
        if (nextSectionIndex > 0) {
          return content.substring(0, nextSectionIndex).trim();
        }
        return content;
      }
    }

    // Fallback: get first version section after Unreleased
    for (const section of lines.slice(1)) {
      if (section.match(/^\d+\.\d+\.\d+\]/)) {
        const contentLines = section.split(/\r?\n/).slice(1);
        const content = contentLines.join('\n').trim();
        const nextSectionIndex = content.indexOf('\n## [');
        console.warn(`Warning: Could not find version ${versionNumber}, using latest release`);
        if (nextSectionIndex > 0) {
          return content.substring(0, nextSectionIndex).trim();
        }
        return content;
      }
    }

    return 'No changelog entries found.';
  } catch (error) {
    console.warn('Warning: Could not read CHANGELOG.md:', error.message);
    return 'Changelog unavailable.';
  }
}

/**
 * Convert CHANGELOG markdown to clean HTML for Telegram
 */
function convertChangelogToHtml(changelogText) {
  let html = changelogText;

  html = html.replace(/^####\s+(🚀|🔧|📚|🎯|📋|✨|💡)\s+(.+)$/gm, '$1 <b>$2</b>');
  html = html.replace(/^###\s+(.+)$/gm, '<b>$1</b>');
  html = html.replace(/^##\s+(.+)$/gm, '<b>$1</b>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  html = html.replace(/`([^`]+?)`/g, '<code>$1</code>');
  html = html.replace(/^(\s*)[-*]\s+/gm, '$1• ');
  html = html.replace(/&/g, '&amp;');
  html = html.replace(/\n\n\n+/g, '\n\n');

  return html.trim();
}

/**
 * Format release message for Telegram (HTML format)
 */
function formatTelegramMessage(releaseInfo, changelogEntries) {
  const emoji = { MAJOR: '🚀', MINOR: '✨', PATCH: '🔧' };
  const icon = emoji[releaseInfo.releaseType] || '📦';

  const changelogHtml = convertChangelogToHtml(changelogEntries);
  const changelogLines = changelogHtml.split('\n').slice(0, 50).join('\n');

  return `${icon} <b>AI Team Template ${releaseInfo.version}</b>

📅 <b>Release Date:</b> ${releaseInfo.releaseDate}
🏷️ <b>Type:</b> ${releaseInfo.releaseType}
📝 <b>Commits:</b> ${releaseInfo.commitCount} commits
🔗 <b>Commit:</b> <code>${releaseInfo.commitHash}</code>

<b>What's New in ${releaseInfo.version}:</b>

${changelogLines}

<b>Links:</b>
🔗 <a href="${REPO_URL}/browse?at=refs%2Ftags%2F${releaseInfo.version}">View Release</a>
📖 <a href="${REPO_URL}/browse/CHANGELOG.md?at=refs%2Ftags%2F${releaseInfo.version}">Full Changelog</a>
📚 <a href="https://confluence.vissoft.vn/pages/viewpage.action?pageId=147624565">User Guide</a>

---
🤖 <b>AI Team Template Maintenance</b>`;
}

/**
 * Send message to Telegram
 */
function sendTelegramMessage(message, chatId) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML',
      disable_web_page_preview: false
    });

    const options = {
      hostname: 'api.telegram.org',
      port: 443,
      path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };

    const req = https.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => { responseData += chunk; });
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(responseData));
        } else {
          reject(new Error(`Telegram API error: ${res.statusCode} - ${responseData}`));
        }
      });
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

/**
 * Main execution
 */
async function main() {
  const mode = isPreviewMode ? 'PREVIEW MODE' : 'TEAM CHANNEL';
  console.log(`Starting release notification (${mode})...\n`);

  console.log('Gathering release information...');
  const releaseInfo = getReleaseInfo();
  console.log(`   Version: ${releaseInfo.version}`);
  console.log(`   Type: ${releaseInfo.releaseType}`);
  console.log(`   Date: ${releaseInfo.releaseDate}`);
  console.log(`   Commits: ${releaseInfo.commitCount}`);

  console.log('\nReading CHANGELOG.md...');
  const changelogEntries = getChangelogEntries();

  console.log('\nFormatting Telegram message...');
  const message = formatTelegramMessage(releaseInfo, changelogEntries);

  const targetChatId = isPreviewMode ? TELEGRAM_PRIVATE_CHAT_ID : TELEGRAM_CHAT_ID;
  const targetDescription = isPreviewMode ? 'private chat for review' : 'TEAM CHANNEL';

  console.log(`\nSending to ${targetDescription}...`);
  try {
    const response = await sendTelegramMessage(message, targetChatId);

    if (isPreviewMode) {
      console.log('Preview sent to private chat!');
      console.log(`   Message ID: ${response.result.message_id}`);
      console.log('');
      console.log('REVIEW THE MESSAGE, then:');
      console.log('   OK:  node scripts/send-release-notification.js --send');
      console.log('   Fix: Fix issue, re-run with --preview');
    } else {
      console.log('Release notification sent!');
      console.log(`   Message ID: ${response.result.message_id}`);
      console.log(`   Chat: ${response.result.chat.title || response.result.chat.id}`);
    }
  } catch (error) {
    console.error('Failed to send:', error.message);
    process.exit(1);
  }

  console.log('\nDone!\n');
}

main().catch((error) => {
  console.error('Unexpected error:', error);
  process.exit(1);
});
