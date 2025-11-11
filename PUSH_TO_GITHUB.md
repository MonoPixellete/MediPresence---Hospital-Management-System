# Push to GitHub - Instructions

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `medipresence` (or your choice)
3. Description: "Hospital Management System with Vercel deployment"
4. Choose Public or Private
5. **DO NOT** check "Initialize with README"
6. Click "Create repository"

## Step 2: Push Your Code

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/medipresence.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Alternative: Using SSH

If you have SSH keys set up:

```bash
git remote add origin git@github.com:YOUR_USERNAME/medipresence.git
git branch -M main
git push -u origin main
```

## Quick Command (Copy and paste after creating repo)

Replace `YOUR_USERNAME` and `REPO_NAME` with your actual values:

```bash
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## Troubleshooting

If you get authentication errors:
1. Use GitHub Personal Access Token instead of password
2. Go to GitHub Settings → Developer settings → Personal access tokens
3. Generate new token with `repo` permissions
4. Use token as password when pushing

