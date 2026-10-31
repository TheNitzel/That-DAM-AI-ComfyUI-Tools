/**
 * publish-github.js
 * Creates the public GitHub repository `ComfyUI-ThatDAMAI` via the GitHub API
 * and pushes the `main` branch when `GITHUB_TOKEN` is set in `.env` or environment.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Load root .env if present
const rootEnv = path.resolve(__dirname, '..', '..', '.env');
if (fs.existsSync(rootEnv)) {
  for (const line of fs.readFileSync(rootEnv, 'utf8').split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith('#')) continue;
    const idx = t.indexOf('=');
    if (idx > 0) {
      const k = t.slice(0, idx).trim();
      const v = t.slice(idx + 1).trim();
      if (!process.env[k]) process.env[k] = v;
    }
  }
}

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
const REPO_NAME = process.env.GITHUB_REPO_NAME || 'ComfyUI-ThatDAMAI';

async function main() {
  if (!GITHUB_TOKEN) {
    console.error('Missing GITHUB_TOKEN in .env or environment.');
    console.error('Add GITHUB_TOKEN=ghp_... to .env and run: node packages/comfyui-thatdamai/publish-github.js');
    process.exit(1);
  }

  console.log('1. Authenticating with GitHub API...');
  const userRes = await fetch('https://api.github.com/user', {
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'ThatDAMAI-Publisher',
    },
  });
  if (!userRes.ok) {
    throw new Error(`GitHub auth failed (${userRes.status}): ${await userRes.text()}`);
  }
  const user = await userRes.json();
  console.log(`   Authenticated as: ${user.login}`);

  console.log(`2. Ensuring public repository ${user.login}/${REPO_NAME} exists...`);
  const createRes = await fetch('https://api.github.com/user/repos', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'User-Agent': 'ThatDAMAI-Publisher',
    },
    body: JSON.stringify({
      name: REPO_NAME,
      description: 'Official ComfyUI Custom Nodes & In-Canvas Browser for That DAM AI (thatdamai.com) — Images, Local Videos & Workflows',
      homepage: 'https://thatdamai.com',
      private: false,
      has_issues: true,
    }),
  });

  if (createRes.status === 201) {
    console.log(`   Created public repository: https://github.com/${user.login}/${REPO_NAME}`);
  } else if (createRes.status === 422) {
    console.log(`   Repository https://github.com/${user.login}/${REPO_NAME} already exists.`);
  } else {
    throw new Error(`Failed to create repo (${createRes.status}): ${await createRes.text()}`);
  }

  console.log('3. Pushing main branch to GitHub...');
  const remoteUrl = `https://x-access-token:${GITHUB_TOKEN}@github.com/${user.login}/${REPO_NAME}.git`;
  const cleanUrl = `https://github.com/${user.login}/${REPO_NAME}.git`;
  try {
    execSync('git remote remove origin', { cwd: __dirname, stdio: 'ignore' });
  } catch (_) {}
  execSync(`git remote add origin "${cleanUrl}"`, { cwd: __dirname, stdio: 'inherit' });
  execSync(`git push -u "${remoteUrl}" main --force`, { cwd: __dirname, stdio: 'inherit' });
  console.log(`\n✅ Published ComfyUI plugin to: https://github.com/${user.login}/${REPO_NAME}`);
}

main().catch(err => {
  console.error('Publish error:', err.message);
  process.exit(1);
});
