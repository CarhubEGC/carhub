#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - David Romero - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for the database to be ready by running a script.
# The database on Render is external and reached over the network, so it is more
# likely to be slow to answer than a sibling container, not less. Without this
# the first mariadb call below fails and "set -e" kills the container on boot.
sh ./scripts/wait-for-db.sh

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations/versions" ]; then
    # Initialize the migration repository
    flask db init
    flask db migrate
fi

# Check if the database is empty
if [ $(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';") -eq 0 ]; then
 
    echo "Empty database, migrating..."

    # Get the latest migration revision
    LATEST_REVISION=$(ls -1 migrations/versions/*.py | grep -v "__pycache__" | sort -r | head -n 1 | sed 's/.*\/\(.*\)\.py/\1/')

    echo "Latest revision: $LATEST_REVISION"

    # Run the migration process to apply all database schema changes
    flask db upgrade

else

    echo "Database already initialized, updating migrations..."

    # Get the current revision to avoid duplicate stamp
    CURRENT_REVISION=$(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT version_num FROM alembic_version LIMIT 1;")
    
    if [ -z "$CURRENT_REVISION" ]; then
        # If no current revision, stamp with the latest revision
        flask db stamp head
    fi

    # Run the migration process to apply all database schema changes
    flask db upgrade
fi

web_command=(gunicorn --bind 0.0.0.0:80 app:app --log-level info --timeout 3600)
fakenodo_url=http://127.0.0.1:5000/api/deposit/depositions

if [[ "${ZENODO_API_URL%/}" != "$fakenodo_url" ]]; then
    exec "${web_command[@]}"
fi

export ZENODO_ACCESS_TOKEN=

gunicorn --bind 127.0.0.1:5000 'fakenodo.app:create_app()' --log-level info &
fakenodo_pid=$!
"${web_command[@]}" &
web_pid=$!

stop_servers() {
    kill -TERM "$web_pid" "$fakenodo_pid" 2>/dev/null || true
    wait "$web_pid" "$fakenodo_pid" 2>/dev/null || true
}

trap 'stop_servers; exit 0' TERM INT

# If either server stops, shut down its sibling and let Render restart the container.
status=0
wait -n "$web_pid" "$fakenodo_pid" || status=$?
stop_servers
exit "$((status == 0 ? 1 : status))"
