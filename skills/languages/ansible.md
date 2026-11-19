

## 1. Rules for agents
- Follow the Ansible version and project layout already in the repo; check official docs for that version before using unfamiliar modules, keywords, or options.
- Prefer built-in modules over `shell` or `command`, and write tasks to be idempotent. Use handlers for actions triggered by configuration changes.
- Use fully qualified collection names (FQCNs) for modules and plugins. Pin role and collection dependencies using the repo's existing `requirements.yml` conventions.
- YAML: use spaces, never tabs; keep indentation consistent with the surrounding playbook. Follow the repo's yamllint configuration rather than inventing formatting rules.
- Never put credentials in playbooks, inventories, or defaults. Use the repo's approved secret mechanism and avoid debug output that could expose secret values.
- Repo configuration wins: don't add or change lint configuration, dependencies, or CI jobs unless asked.

## 2. Official references
- Ansible best practices: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_best_practices.html
- Ansible playbooks: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html
- Ansible collections: https://docs.ansible.com/ansible/latest/collections_guide/collections_installing.html
- `ansible-lint`: https://docs.ansible.com/projects/lint/
- `yamllint`: https://yamllint.readthedocs.io/en/stable/

## 3. Lint and validate before proposing a change
Run the checks configured by the repo or CI first. If available and consistent with that configuration:

```bash
ansible-lint
yamllint .
ansible-playbook --syntax-check <playbook.yml>
```

Use the repo's inventory, installed collections, and dependency setup when syntax checking requires them. Don't install tools or add configuration just to make these commands run.

## 5. Keeping current
- Recheck official docs when Ansible versions change; use the documentation matching the version pinned by the repo.