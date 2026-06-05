## Developer reset (`nuke_db.sh`)

For local development only, you can fully reset the database state (local `storage` and Docker volume):

```bash
./scripts/nuke_db.sh
```

Optional flags:

```bash
./scripts/nuke_db.sh --local-only
./scripts/nuke_db.sh --docker-only
./scripts/nuke_db.sh --yes
```