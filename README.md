### Manual Database Migrations

To manually apply database migrations in your production environment, follow these steps:

1. **List Running Containers:**

    ```bash
    docker ps
    ```

    Find the container ID or name of your running Flask application.

2. **Run Database Migrations:**

    ```bash
    docker exec -it <your-container-id-or-name> flask db upgrade
    ```

    Replace `<your-container-id-or-name>` with the actual container ID or name.

This will apply any pending migrations to your database inside the running container.
