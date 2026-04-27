# Release Report Example - Version 1.2.2

**This is an example of what the Telegram notification will contain.**

---

🔧 **AI Team Template 1.2.2-RELEASE**

📅 **Release Date:** 2026-01-27
🏷️ **Type:** PATCH
📝 **Commits:** 2 commits
🔗 **Commit:** b913109

**Version 1.2.2 - Enhanced project-setup skill**

## What's New

### Enhanced

#### `/project-setup` Skill - Improved Existing Project Workflow
- **Enhanced `/project-setup` command** for better existing project integration
  - **NEW**: Prompts user to input full path to existing project directory
  - **NEW**: Automatically navigates to provided directory using `cd` command
  - **Benefit**: Team members can run `/project-setup` from template directory, no need to manually navigate
  - **Workflow improvement**:
    1. Clone AI Team Template repository (anywhere)
    2. Run `/project-setup` from template directory
    3. Choose "Existing Project" option
    4. Provide full path to existing project (e.g., `D:\my-projects\backend-api`)
    5. Claude navigates to that directory and sets up template automatically
  - **User experience**: Simpler workflow, reduced setup errors
  - **Documentation updated**:
    - `.claude/skills/project-setup/SKILL.md` - Added directory prompt flow
    - `README.md` - Updated quick start instructions
    - `CHANGELOG.md` - Documented enhancement
  - **Platform support**: Windows (`D:\path`), Linux/Mac (`/home/user/path`)
  - **Error handling**: Directory verification, permission checks, path validation
  - **Backward compatible**: Existing functionality unchanged

### Changed

#### Documentation Improvements
- **`.gitignore`** - Added ignore patterns for generated output files
  - Code review reports (`docs/reviews/*.md`)
  - Bug reports (`docs/bugs/*.md`)
  - Agent handoff reports (`docs/handoffs/*.md`)
  - Test reports already ignored (existing)
  - All `.gitkeep` files preserved for directory structure

---

🔗 **[View Release](https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team/browse?at=refs%2Ftags%2F1.2.2-RELEASE)**
📖 **[Full Changelog](https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team/browse/CHANGELOG.md?at=refs%2Ftags%2F1.2.2-RELEASE)**

---

_Released by AI Team Template Maintainers_

---

## Notes

**This message format is sent to:**
- Telegram channel/group configured in environment variables
- Audience: Development team, stakeholders

**Customization:**
- Edit `scripts/send-release-notification.js` to customize format
- Change emoji icons, message structure, or content length
- See `docs/TELEGRAM_NOTIFICATION_SETUP.md` for details

**Frequency:**
- Sent once per release
- Triggered manually after pushing to remote: `node scripts/send-release-notification.js`
- Can be integrated into CI/CD pipeline for full automation
