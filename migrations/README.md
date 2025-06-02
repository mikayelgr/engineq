# Database Migration Best Practices

This document outlines best practices for creating and managing database migrations using `dbmate` for this project.

## Guiding Principles

1.  **Reversibility is Key:** Every migration *must* have a corresponding `migrate:down` script that accurately reverses the `migrate:up` operations. This is crucial for development stability, testing, and safe rollbacks in production if issues arise.
2.  **Atomicity (where possible):** Each migration should represent a single, logical change to the database schema.
3.  **Clarity and Readability:** Migration names and SQL code should be clear and easy to understand.

## Creating Migrations

*   **Naming Convention:** Use the format `YYYYMMDDHHMMSS_descriptive_name.sql`. `dbmate` generates the timestamp; you provide the descriptive name.
    *   Example: `dbmate new add_user_email_column` will create something like `20231027103000_add_user_email_column.sql`.
*   **`migrate:up` Script:** Contains the SQL commands to apply the new schema changes.
*   **`migrate:down` Script:** Contains the SQL commands to completely reverse the `migrate:up` script. Test this locally!

## Best Practices

### 1. Always Write a `migrate:down` Script
   Before considering a migration complete, write and test its `down` script. If a migration is inherently destructive and data cannot be preserved (e.g., dropping a column that is no longer needed), the `down` script should still attempt to restore the *schema* to its previous state, even if data is lost. Document any data loss implications.

### 2. Explicitly Name Constraints and Indexes
   When creating constraints (Primary Key, Foreign Key, Unique, Check) or Indexes, provide an explicit name. This makes them easier to reference, modify, or drop in future migrations.
   *   **Bad (auto-named index):** `CREATE INDEX ON users (email);`
   *   **Good:** `CREATE INDEX idx_users_email ON users (email);`
   *   **Bad (auto-named FK):** `ALTER TABLE posts ADD COLUMN user_id INT REFERENCES users(id);`
   *   **Good:** `ALTER TABLE posts ADD COLUMN user_id INT, ADD CONSTRAINT fk_posts_user_id FOREIGN KEY (user_id) REFERENCES users(id);`

### 3. Separate Schema Changes from Data Migrations
   *   **Schema Migrations:** Focus on `CREATE`, `ALTER`, `DROP` statements for tables, columns, indexes, constraints, etc. These are generally quick to run.
   *   **Data Migrations:** If you need to update existing data, backfill new columns, or perform transformations, consider these separately:
        *   For simple data updates that are quick and low-risk, they can sometimes be included in the schema migration (e.g., setting a default value for a new non-null column on existing rows).
        *   For complex, long-running, or risky data migrations:
            *   Preferably handle these via application-level scripts or tasks that can be run independently of schema deployment. This allows for better error handling, retries, and monitoring.
            *   If they *must* be in a migration, clearly document their purpose and potential impact. Ensure they are idempotent if possible.

### 4. Test Migrations Locally
   *   Run `dbmate up` to apply your new migration.
   *   Run `dbmate down` to test the rollback.
   *   Run `dbmate up` again to leave the schema in the desired state.
   *   Check `dbmate status` to see the state of applied migrations.

## Common `dbmate` Commands

The `dbmate` tool is managed via scripts in the `migrator/` directory (or will be, post-refactor). Assuming `dbmate` is accessible:

*   **Create a new migration:**
    ```bash
    dbmate -d ./migrations new your_migration_name
    ```
    (Replace `your_migration_name` with a descriptive name, e.g., `add_indices_to_user_table`)
*   **Apply pending migrations:**
    ```bash
    dbmate -d ./migrations up
    ```
*   **Rollback the last migration:**
    ```bash
    dbmate -d ./migrations down
    ```
*   **Rollback all migrations:**
    ```bash
    dbmate -d ./migrations drop # CAUTION: This drops all tables in the DB!
    # Then re-apply all:
    dbmate -d ./migrations up
    ```
*   **View migration status:**
    ```bash
    dbmate -d ./migrations status
    ```

## Example Migration Structure

```sql
-- migrate:up
CREATE TABLE example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_example_table_name ON example_table (name);

-- migrate:down
DROP INDEX IF EXISTS idx_example_table_name;
DROP TABLE IF EXISTS example_table;
```

## Environment & Deployment Considerations

### Database Container (PostgreSQL)

For local development, testing, and consistent deployments, it is highly recommended to use a PostgreSQL container.

*   **Docker:** You can use the official PostgreSQL image from Docker Hub.
    ```bash
    # Example: Run PostgreSQL for local development
    docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_USER=myuser -e POSTGRES_DB=mydb -p 5432:5432 -d postgres
    ```
    Ensure the port, user, password, and database name match your configuration.

*   **Docker Compose:** If you use Docker Compose for managing your services, include a PostgreSQL service in your `docker-compose.yml`:
    ```yaml
    # Example: services section in docker-compose.yml
    services:
      postgres_db:
        image: postgres:latest # Or a specific version
        container_name: my_postgres_container
        environment:
          POSTGRES_USER: your_db_user
          POSTGRES_PASSWORD: your_db_password
          POSTGRES_DB: your_database_name
        ports:
          - "5432:5432" # Map host port to container port
        volumes:
          - postgres_data:/var/lib/postgresql/data # Optional: for data persistence
    # ... other services ...

    volumes: # Optional: for data persistence
      postgres_data:
    ```

### Environment Variables

Properly configuring environment variables is crucial for database migrations and application connectivity.

#### For `dbmate` (Migrator)

The `dbmate` tool typically uses the `DATABASE_URL` environment variable to connect to the database. The provided `migrator/.env.example` shows variables like `LOCAL`, `STAGING`, `PRODUCTION`. These can be used with `dbmate` by:
1. Setting `DATABASE_URL` directly.
2. Using `dbmate`'s `-e <env_name>` flag if `dbmate` is configured to read specific .env files or sections (this depends on the exact `dbmate` setup which is being refactored).
3. Passing the URL directly via the `--url` or `-u` flag: `dbmate -u "postgresql://user:pass@host/db" ...`

*   **`DATABASE_URL`**: The connection string for `dbmate`.
    *   *Example (for local development, matching `migrator/.env.example`'s `LOCAL` variable):*
        `DATABASE_URL="postgresql://postgres:postgres@localhost:5432/engineq?sslmode=disable"`

#### For Acura Application (Database Interaction & Model Generation)

The Acura application and its associated scripts (like model generation) use the `POSTGRES_URL`.

*   **`POSTGRES_URL`**: The connection string used by SQLAlchemy and `sqlacodegen`.
    *   *Example (from `acura/.env.example`):*
        `POSTGRES_URL="postgresql+asyncpg://postgres:postgres@localhost:5431/engineq"`

    *Note on Ports:* The example URLs (`DATABASE_URL` for `dbmate` and `POSTGRES_URL` for Acura) show different ports (5432 vs. 5431). Ensure these are set correctly for your environment. If they target the same database instance, the port should typically be the same. If they are for different proxy/direct connections, document accordingly.

**Key variables to define in your environment (e.g., in `.env` files at `acura/.env` and `migrator/.env` or your deployment environment):**

*   `DATABASE_URL` (for `dbmate` / `migrator` tool)
*   `POSTGRES_URL` (for `acura` application and scripts)

Ensure these URLs point to your running PostgreSQL instance with the correct credentials, host, port, and database name.

By following these guidelines, we can maintain a healthy, reliable, and manageable database schema.
