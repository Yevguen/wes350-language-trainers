from main import app

for r in app.routes:
    methods = "|".join(sorted(getattr(r, "methods", []))) or "MOUNT"
    print(f"{methods:7} {r.path}")