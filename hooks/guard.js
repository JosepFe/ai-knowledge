// PreToolUse: deny cluster/infra/Vault changes and secret reads (user runs them), ask for local state changes,
// auto-allow read-only file/MCP/terminal calls that can't return secret material.
let raw = '';
process.stdin.on('data', d => (raw += d)).on('end', () => {
  const e = JSON.parse(raw || '{}');
  const tool = String(e.tool_name || '');
  const input = e.tool_input || {};
  const json = JSON.stringify(input);

  const decide = (decision, reason) => {
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: decision, permissionDecisionReason: `certman-guard: ${reason}` }
    }));
    process.exit(0);
  };

  // Output caps: deny unbounded reads; the model retries with a bound.
  const capped = (re, ok, why) => { if (re.test(tool) && !ok) decide('deny', `Output cap: ${why}`); };
  capped(/kubectl_logs$/i, input.tail <= 200 || input.since || input.sinceTime, 'pass tail <= 200, or since.');
  capped(/get_pipeline_job_output$/i, input.limit <= 300, 'pass limit <= 300 (lines from the end); page back with offset.');
  capped(/search_code$/i, input.perPage <= 20, 'pass perPage <= 20 and only the fields you need.');

  if (/kubectl_(apply|delete|patch|scale|create|rollout)|helm_chart|node_management|kubernetes_cleanup|^cleanup$/i.test(tool)) {
    decide('deny', `${tool} changes the cluster. Output the command for the user to run.`);
  }
  if (/_write|update_dashboard|update_datasource|create_folder|create_datasource|exec_in_pod|port_forward|kubectl_generic/i.test(tool)) {
    decide('ask', `${tool} writes data or opens a session.`);
  }
  if (!/replace|create|edit|write/i.test(tool) && /(\.copilot|\.config[\\/]+ai-knowledge)[\\/]+local|\.ado-mcp\.env|\.mcp-auth|\.copilot[\\/]+(mcp-config\.json|mcp-oauth-config)|Code[\\/]+User[\\/]+mcp\.json|\.aws[\\/]+(credentials|sso)|Code[\\/]+User[\\/]+History/i.test(json)) {
    decide('deny', 'secret files (MCP tokens, AWS credentials, VS Code history) are off-limits to the agent.');
  }

  const secretRead = /\bkubectl\b[^|;&\r\n]*\sget\s+secrets?\b|"(resourceType|kind|resource)"\s*:\s*"secrets?"|get-secret-value|get-parameters?\b[^|;&\r\n]*--with-decryption|\bvault\b[^|;&\r\n]*\s(read|kv\s+get)\b|\b(glab\s+variable|gh\s+secret)\b|keyvault\s+secret|pipeline_variables|\.(pfx|p12|key|pem|env)\b|credentials|kubeconfig|id_rsa/i;
  if (!/terminal|bash|powershell|shell|call_aws/i.test(tool)) {
    const readTool = /read_?file|list_?dir|grep_?search|file_?search|semantic_?search|list_?code_?usages|get_?terminal_?output|(^|_)(get|list|search|read|query|find|describe|explain|logs|whoami|health_check|discover_tools|ping|check|analyze|generate_deeplink|retrieve|suggest|diff)(_|$)/i;
    const writeTool = /write|create|update|delete|apply|patch|scale|exec|install|rollout|cleanup|merge|approve|retry|cancel|play|trigger|push|fork|unlock|forward|reconnect|manage|generic|api_request|context|wait_for|node_management/i;
    // A subagent brief is prose that may mention credentials/kubeconfig; its own tool calls are checked on their own.
    if (/subagent/i.test(tool)) decide('allow', `${tool} only delegates.`);
    // GitLab/GitHub MCP reads never ask (CI variables excepted); the first verb in the tool name decides (get_merge_request is a read, merge_merge_request is not).
    if (/(gitl|github)/i.test(tool) && !/pipeline_variables/i.test(tool)) {
      const verb = tool.toLowerCase().split(/[_\/.:-]/).find(t => /^(get|list|search|read|discover|whoami|health|wait|validate|create|update|delete|merge|approve|unapprove|push|fork|cancel|retry|rerun|play|trigger|run|write|add|remove|close|edit|publish|upload|dismiss|assign|reply|submit|lock|unlock|star|mark|set|resolve|manage|execute|erase|archive)$/.test(t));
      if (/^(get|list|search|read|discover|whoami|health|wait|validate)$/.test(verb || '')) decide('allow', `${tool} is a read-only GitLab/GitHub call.`);
    }
    if (secretRead.test(tool) || secretRead.test(json)) decide('ask', `${tool} may return secret material.`);
    // vSphere MCP (futuretea/vsphere-mcp-server) exposes only read tools.
    if (/vsphere_(list|get|query)_/i.test(tool)) decide('allow', `${tool} is a read-only vSphere call.`);
    if (readTool.test(tool) && !writeTool.test(tool)) decide('allow', `${tool} is read-only.`);
    process.exit(0);
  }

  let cmd = [input.command, input.cli_command, input.input, input.text].filter(Boolean).join('\n');
  if (!cmd.trim()) cmd = json;

  const deny = {
    'terraform/terragrunt apply, destroy, import or state change': /\b(terraform|terragrunt|tofu)\b[^|;&\r\n]*\s(apply|destroy|import|force-unlock|state\s+(rm|mv|push|replace-provider))\b/,
    'kubectl change': /\bkubectl\b[^|;&\r\n]*\s(apply|delete|patch|scale|edit|replace|drain|cordon|uncordon|annotate|label|taint|rollout\s+(restart|undo))\b/,
    'helm release change': /\bhelm\b[^|;&\r\n]*\s(install|upgrade|uninstall|rollback|delete)\b/,
    'Vault write': /\bvault\b[^|;&\r\n]*\s(write|delete|destroy|put|patch|enable|disable|tune)\b/
  };
  const ask = {
    'git state change': /\bgit\b[^|;&\r\n]*\s(push|commit|reset|rebase|checkout|switch|stash|cherry-pick|tag|merge|clean|restore)\b/,
    'AWS change': /\baws\b[^|;&\r\n]*\s(create|delete|put|update|modify|terminate|run|start|stop|attach|detach|reboot|remove|revoke|authorize|register|deregister)-[a-z]/,
    'S3 write': /\baws\s+s3\s+(rm|mv|cp|sync|rb|mb)\b/,
    'Alibaba change': /\baliyun\b[^|;&\r\n]*\s(Create|Delete|Modify|Update|Put|Remove|Attach|Detach|Stop|Start|Reboot)[A-Z]/,
    'recursive delete': /\brm\s+-[a-z]*r|Remove-Item\b[^|;&\r\n]*-Recurse/
  };
  for (const [name, re] of Object.entries(deny)) if (re.test(cmd)) decide('deny', `${name} is blocked. Output the command for the user to run.`);
  // AWS CLI must name the account explicitly; the default profile may point anywhere.
  const unquoted = cmd.replace(/'[^']*'|"[^"]*"/g, '""');
  if (/(^|[;|&({])\s*aws(\.exe)?\s+(?!--version\b|help\b|configure\s+list)[a-z]/im.test(unquoted) && !/--profile[\s=]|AWS_PROFILE/i.test(cmd)) {
    decide('deny', 'AWS command without --profile <env> (dev, stage, prod, qa). Add it and retry.');
  }
  if (/\bkubectl\b[^|;&\r\n]*\slogs\b/i.test(cmd)) {
    const tail = Number((cmd.match(/--tail[= ](\d+)/) || [])[1]);
    if (!(tail <= 200) && !/--since(-time)?[= ]/.test(cmd)) decide('deny', 'Output cap: add --tail=200 or less, or --since=15m.');
  }
  // Read-looking commands that print a live credential: always a second, explicit confirmation.
  const credentialPrinters = /\baws\b[^|;&\r\n]*\s(ecr\s+get-login-password|ecr-public\s+get-login-password|eks\s+get-token|sts\s+(get-session-token|assume-role\S*|get-federation-token)|configure\s+export-credentials|codeartifact\s+get-authorization-token)\b|\b(terraform|terragrunt|tofu)\b[^|;&\r\n]*\s(output\b[^|;&\r\n]*-(json|raw)|show\b[^|;&\r\n]*-json)|\bhelm\b[^|;&\r\n]*\sget\s+(values|all|manifest)\b|\bkubectl\b[^|;&\r\n]*\sconfig\s+view\b[^|;&\r\n]*--raw|\bvault\b[^|;&\r\n]*\s(print\s+token|token\s+create)\b/i;
  if (credentialPrinters.test(cmd)) decide('ask', 'DANGER: this command prints a live credential (password/token/state secrets) into the output and the chat. Approve only if you really need it.');
  // Repos listed in local/guard-trusted-git.json (path prefixes, ~ allowed) skip the git ask for commit (no --amend) and merge --ff-only.
  const os = require('os'), fs = require('fs'), path = require('path');
  const expand = p => p.replace(/^~/, os.homedir());
  let trusted = [];
  try { trusted = JSON.parse(fs.readFileSync(path.join(os.homedir(), '.config', 'ai-knowledge', 'local', 'guard-trusted-git.json'), 'utf8')).map(expand); } catch {}
  const gitDir = expand((cmd.match(/\bgit\s+-C\s+"?([^\s"]+)/) || cmd.match(/\bcd\s+"?([^\s"&;]+)"?\s*&&/) || [])[1] || e.cwd || '');
  const gitOps = cmd.match(new RegExp(ask['git state change'].source + String.raw`[^|;&\r\n]*`, 'g')) || [];
  const trustedGit = gitOps.length > 0 && trusted.some(p => path.resolve(gitDir).startsWith(path.resolve(p)))
    && gitOps.every(s => /\s(commit(?![^|;&\r\n]*--amend)|merge\s+--ff-only)\b/.test(s));
  for (const [name, re] of Object.entries(ask)) if (re.test(cmd) && !(name === 'git state change' && trustedGit)) decide('ask', `${name}.`);
  if (secretRead.test(cmd)) decide('ask', 'command may print secret material.');
  if (/call_aws/i.test(tool) && /--profile[\s=]+prod\b/.test(cmd)) decide('ask', 'AWS MCP call against prod.');

  // Quoted text can't run anything, except "$(...)" subexpressions, which are kept and checked.
  const bare = cmd.replace(/'[^']*'/g, "''").replace(/"[^"]*"/g, m => (m.includes('$(') ? m : '""'));
  const writes = /\b(Out-File|Tee-Object|tee|Set-(?!Location\b)\w+|Add-Content|New-Item|Remove-\w+|Copy-Item|Move-Item|Rename-Item|Clear-\w+|Invoke-Expression|iex|Invoke-WebRequest|Invoke-RestMethod|Start-Process|Stop-Process)\b|\.(Delete|Write\w*|Remove\w*|Kill|Save\w*|Create\w*|Move\w*|Copy\w*|Start|Stop|Invoke\w*)\s*\(|(?<![&>])&(?![&1])|\$env:\w+\s*=|\s-out\b|(?<![2*])>(?!&1|\s*\$null)/i;
  if (writes.test(bare)) process.exit(0);

  const flags = String.raw`(?:-\S+(?:\s+[^-\s]\S*)?\s+)*`;
  const cli = (bin, verbs) => new RegExp(String.raw`^(?:${bin})(?:\.exe)?\s+${flags}(?:${verbs})(?:\s|$)`, 'i');
  const readCmds = [
    // PowerShell control keywords; their bodies are split into separate segments and checked on their own.
    /^(if|elseif|else|try|catch|finally|foreach|for|while|switch)(\s|\(|$)/i,
    /^(get|select|where|foreach|sort|measure|format|test|resolve|join|split|convertfrom|convertto|compare|group)-\w+(\s|$)/i,
    /^(set-location|push-location|pop-location|out-string|write-host|write-output|cd|ls|dir|gci|gc|sls|pwd|cat|type|echo|grep|rg|findstr|head|tail|wc|jq|yq|sort|uniq|cut|tree|where|select|ft|fl|%|\?|foreach|if|else|elseif|in|base64|nslookup|dig)(\s|$)/i,
    /^[$'"\d@,\-+]/,
    cli('git', String.raw`status|diff|log|show|rev-parse|ls-files|ls-remote|blame|describe|grep|branch(?![^|;\r\n]*\s-[dDmMcC]\b)|remote(?!\s+(add|remove|rm|rename|set-url|prune))`),
    cli('kubectl', String.raw`get|describe|logs|top|explain|api-resources|api-versions|version|cluster-info|auth\s+can-i|config\s+(view|get-contexts|current-context)`),
    cli('helm', 'list|ls|status|get|history|template|lint|show|search|version|env'),
    cli('terraform|terragrunt|tofu', String.raw`validate|plan|output|show|providers|version|graph|fmt\s+-check|hclfmt\s+--check|hcl\s+(fmt\s+--check|validate)|run-all\s+(plan|validate|output)|run\s+--all\s+(plan|validate|output)`),
    cli('aws', String.raw`sts\s+get-caller-identity|s3\s+ls|configure\s+list|\S+\s+(describe|list|get)-[\w-]+`),
    /^az(\s+[a-z][\w-]*)+?\s+(show|list|query)(\s|$)/i,
    cli('gh', String.raw`(pr|issue|run|release|workflow|repo|label|cache)\s+(list|view|status|diff|checks)|auth\s+status`),
    cli('glab', String.raw`(mr|issue|ci|pipeline|release|repo|job)\s+(list|view|status|diff|trace|get)|auth\s+status`),
    cli('vault', String.raw`status|version|token\s+lookup|list|kv\s+list|policy\s+(read|list)|auth\s+list|secrets\s+list`),
    cli('openssl', 'x509|s_client|crl|req|verify|asn1parse|version'),
    // The wrapper refuses any govc command that isn't a read.
    /^\S*[\\/]vsphere-govc-read-only[\\/]govc\.ps1(\s|$)/i,
    /^node\s+\S*[\\/]knowledge-search[\\/]search\.js(\s|$)/i
  ];
  const segments = bare.split(/&&|\|\||[;|\r\n{}()]/)
    .map(s => s.trim().replace(/^\$[\w.]+\s*=\s*/, ''))
    .filter(Boolean);
  if (segments.length && segments.every(s => readCmds.some(re => re.test(s)))) decide('allow', 'read-only command.');
});
