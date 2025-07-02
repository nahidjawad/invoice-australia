# Resetting the Database (Development & Production)

If you want to drop all data and recreate your database from scratch (for example, after a schema change), follow these steps. **This will delete all invoice and user data.**

---

## 1. Delete the SQLite Database File

By default, the database is stored at `instance/invoices.db`.

```bash
rm -f instance/invoices.db
```

---

## 2. Recreate the Database Tables

Activate your virtual environment if it is not already active:

```bash
source venv/bin/activate
```

Then run this command to create all tables with the latest schema:

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## 3. Summary of Commands

```bash
rm -f instance/invoices.db
source venv/bin/activate
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## Notes
- This process works for both development and production environments.
- All data will be lost. Only do this if you are sure you do not need any existing data.
- If you use a different database (e.g., PostgreSQL, MySQL), the process will be different. 