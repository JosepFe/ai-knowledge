// SessionStart: tell the user when a pinned MCP server in the private template has a newer release (registries checked once a day).
const fs = require('fs');
const os = require('os');
const path = require('path');

const localDir = path.join(os.homedir(), '.config', 'ai-knowledge', 'local', 'mcp');
const template = path.join(localDir, 'mcp.template.jsonc');
const cache = path.join(localDir, 'mcp-updates.json');

const getJson = async url => (await fetch(url, { signal: AbortSignal.timeout(5000) })).json();
const newer = (a, b) => {
  const [x, y] = [a, b].map(v => v.split('.').map(Number));
  for (let i = 0; i < 3; i++) if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0);
  return false;
};

const latest = {
  npm: async pkg => (await getJson(`https://registry.npmjs.org/${pkg.replace('/', '%2f')}/latest`)).version,
  pypi: async pkg => (await getJson(`https://pypi.org/pypi/${pkg}/json`)).info.version,
  image: async repo => (await getJson(`https://hub.docker.com/v2/repositories/${repo}/tags?page_size=50`)).results
    .map(t => t.name).filter(t => /^\d+\.\d+\.\d+$/.test(t)).reduce((a, b) => (newer(b, a) ? b : a))
};

const pins = () => {
  const servers = JSON.parse(fs.readFileSync(template, 'utf8').replace(/^\s*\/\/.*$/gm, '')).servers;
  const found = [];
  for (const [server, s] of Object.entries(servers)) {
    const registry = { npx: 'npm', uvx: 'pypi', podman: 'image', docker: 'image' }[s.command];
    for (const arg of s.args || []) {
      const m = registry === 'image'
        ? arg.match(/^(?:docker\.io\/)?([\w.-]+\/[\w.-]+):(\d[\w.-]*)$/)
        : arg.match(/^(@?[^@=\s]+)(?:@|==)(\d[\w.-]*)$/);
      if (registry && m) found.push({ server, registry, pkg: m[1], pinned: m[2] });
    }
  }
  return found;
};

(async () => {
  if (!fs.existsSync(template)) return;
  const current = pins();
  let state = {};
  try { state = JSON.parse(fs.readFileSync(cache, 'utf8')); } catch {}
  if (!state.checked || Date.now() - state.checked > 24 * 3600 * 1000) {
    const results = await Promise.all(current.map(async p => ({ ...p, latest: await latest[p.registry](p.pkg).catch(() => null) })));
    state = { checked: Date.now(), updates: results.filter(r => r.latest && newer(r.latest, r.pinned)) };
    try { fs.mkdirSync(path.dirname(cache), { recursive: true }); fs.writeFileSync(cache, JSON.stringify(state, null, 2)); } catch {}
  }
  // Drop cached entries whose pin was bumped since the last check.
  const updates = (state.updates || []).filter(u => current.some(p => p.pkg === u.pkg && p.pinned === u.pinned));
  if (!updates.length) return;
  process.stdout.write(JSON.stringify({
    systemMessage: `MCP updates available: ${updates.map(u => `${u.server} (${u.pkg} ${u.pinned} -> ${u.latest})`).join(', ')}. Review the release notes, then bump the pin in your private template and your mcp.json.`
  }));
})();
