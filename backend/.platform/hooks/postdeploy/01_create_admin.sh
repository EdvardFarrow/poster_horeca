#!/bin/bash
set -e

echo "Running postdeploy hook: 01_create_admin.sh"


INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
LEADER_ID=$(/opt/elasticbeanstalk/bin/get-config environment -k LEADER_INSTANCE)

if [ "$INSTANCE_ID" = "$LEADER_ID" ]; then
    echo "This is the leader instance. Running admin creation..."
    
    source /var/app/venv/bin/activate
    
    cd /var/app/current/
    
    python3 manage.py create_admin --role=owner
    
    echo "Admin creation script finished."
else
    echo "This is not the leader. Skipping admin creation."
fi