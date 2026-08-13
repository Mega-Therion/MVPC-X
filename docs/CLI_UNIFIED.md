# Unified CLI

```bash
python -m mvpc.cli_bridge nexus audit
python -m mvpc.cli_bridge nexus si-check --lhs F --rhs m:1.0,a:1.0
python -m mvpc.cli_bridge harden --code 'theorem t : True := by trivial'
python -m mvpc.cli_bridge legacy --help
```

```toml
[project.scripts]
mvpc = "mvpc.cli_bridge:main"
mvpc-nexus = "mvpc.nexus_cli:main"
```
