# GitHub Pages Setup for ImageFox Comparison

## Your Setup
- **Repository**: github.com/chubajs/imagefox
- **Page URL**: https://chubajs.github.io/imagefox/

## Quick Setup (3 minutes)

### Step 1: Enable GitHub Pages
1. Go to https://github.com/chubajs/imagefox
2. Click **Settings** tab
3. Scroll to **Pages** section (left sidebar)
4. Under **Source**, select **GitHub Actions**

### Step 2: Push the files
```bash
git add public/index.html .github/workflows/deploy-pages.yml
git commit -m "Deploy ImageFox comparison page to GitHub Pages"
git push origin main
```

### Step 3: Access Your Page
After ~2-3 minutes, your page will be live at:
```
https://chubajs.github.io/imagefox/
```

## What's Included

1. **`public/index.html`** - Your comparison page
2. **`.github/workflows/deploy-pages.yml`** - Automatic deployment workflow

## How It Works

Every time you push to `main`:
1. GitHub Actions workflow triggers
2. Deploys the `public` folder to GitHub Pages
3. Page updates automatically in 2-3 minutes

## Direct Links to Share

Once deployed:
- Main comparison: https://chubajs.github.io/imagefox/
- Grid view: https://chubajs.github.io/imagefox/#grid
- Voting mode: https://chubajs.github.io/imagefox/#comparison
- Results table: https://chubajs.github.io/imagefox/#table

## Updating Content

To update the comparison page:
```bash
# Edit the original file
nano imagefox_comparison.html

# Copy to public folder
cp imagefox_comparison.html public/index.html

# Commit and push
git add public/index.html
git commit -m "Update comparison page"
git push origin main
```

## Check Deployment Status

1. Go to https://github.com/chubajs/imagefox/actions
2. Look for "Deploy to GitHub Pages" workflow
3. Green checkmark = successfully deployed

## Share Message

```
🚀 ImageFox Experiment Results are LIVE!

We analyzed the same easyJet article through 20 different analytical approaches.
Each produced unique image selections.

Vote here: https://chubajs.github.io/imagefox/

Our AI picked:
🥇 Risk Assessment (85.10/10)
🥈 Brand Management (84.06/10)
🥉 Communication Strategy (83.96/10)

Will human votes match AI analysis? Let's find out!
```