# Skills Browser - GitHub Pages Site

**This directory contains the GitHub Pages website for browsing Claude Code skills.**

**⚠️ Not to be confused with:**

- `/documentation/` - Templates for **generating** documentation (docstrings, API docs, etc.)

- `/guides/` - User guides (QUICKSTART, TEMPLATE_FINDER, DECISION_TREES)

---

Web-based interface for browsing and discovering Claude Code skills from the AI Templates repository.

## Live Demo

Once deployed to GitHub Pages, this will be available at:
`https://[your-username].github.io/ai_templates/`

## Setup GitHub Pages

1. **Push to GitHub:**
   ```bash
   git add docs/ skills.json
   git commit -m "Add skills browser and catalog"
   git push origin main
   ```

2. **Enable GitHub Pages:**

   - Go to repository Settings

   - Navigate to "Pages" section

   - Under "Source", select "Deploy from a branch"

   - Select branch: `main`

   - Select folder: `/docs`

   - Click "Save"

3. **Wait for deployment:**

   - GitHub will build and deploy automatically

   - Takes 1-2 minutes

   - Check the Pages section for the live URL

## Features

### Search and Filter
- **Search:** Type in skill name or description

- **Category Filter:** Browse by category (Workflow, Documentation, etc.)

- **Priority Filter:** Filter by CRITICAL, HIGH, MEDIUM, LOW

- **Language Filter:** Find skills for specific programming languages

### Skill Cards
Each skill displays:

- Name and description

- Category and priority badge

- Language support

- Size metrics (lines, tokens)

- Required tools

- Install button

### Installation Modal
Click any skill card to see:

- Detailed skill information

- Installation command

- Copy-to-clipboard functionality

- Complete metadata

## Local Development

To test locally:

```bash
# Option 1: Python HTTP server
cd docs
python -m http.server 8000

# Option 2: Node.js http-server
npm install -g http-server
cd docs
http-server

# Then visit: http://localhost:8000
```

## File Structure

```
docs/
├── index.html          # Main browser interface
└── README.md           # This file

../skills.json          # Skills catalog (referenced by index.html)
```

## Customization

### Updating Styles

Edit the `<style>` section in `index.html`:

- Colors: Modify CSS variables at top

- Layout: Adjust grid template in `.skills-grid`

- Responsive: Modify media queries at bottom

### Adding Features

The JavaScript code at bottom of `index.html` handles:

- `loadSkills()` - Fetches and parses skills.json

- `displaySkills()` - Renders skill cards

- `filterSkills()` - Search and filter logic

- `showInstallModal()` - Installation details

## Maintenance

### After Adding New Skills

1. **Rebuild catalog:**
   ```bash
   python tools/build_skills_catalog.py
   ```

2. **Commit and push:**
   ```bash
   git add skills.json
   git commit -m "Update skills catalog"
   git push origin main
   ```

3. **GitHub Pages auto-updates** (no additional action needed)

### Updating Browser

1. **Edit `docs/index.html`**

2. **Test locally** (see Local Development above)

3. **Push changes:**
   ```bash
   git add docs/index.html
   git commit -m "Update skills browser"
   git push origin main
   ```

## Browser Compatibility

Tested and working on:

- ✅ Chrome/Edge (latest)

- ✅ Firefox (latest)

- ✅ Safari (latest)

- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Loads all skills at once (48 skills = ~200KB JSON)

- Client-side filtering (instant results)

- No backend required

- Works offline after initial load

## Future Enhancements

Potential additions:

- [ ] Skill comparison feature

- [ ] Installation history tracking

- [ ] Favorites/bookmarks

- [ ] Dark mode toggle

- [ ] Advanced search (tags, tools)

- [ ] Related skills recommendations

- [ ] Download statistics (if tracking added)

---

*Skills Browser v1.0.0 - Part of AI Templates v0.2.6*
