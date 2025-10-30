#!/bin/bash
set -e

echo "Running postdeploy hook: 01_create_admin.sh"

IS_SINGLE_INSTANCE=$(/opt/elasticbeanstalk/bin/get-config environment -k EB_IS_SINGLE_INSTANCE || true)

RUN_COMMAND=false

if [ "$IS_SINGLE_INSTANCE" = "true" ]; then
  echo "This is a Single Instance environment. Running admin creation..."
  RUN_COMMAND=true

else
  echo "This is a Load-Balanced environment. Checking for leader..."
  INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
  LEADER_ID=$(/opt/elasticbeanstalk/bin/get-config environment -k LEADER_INSTANCE || true)
  
  if [ "$INSTANCE_ID" = "$LEADER_ID" ]; then
    echo "This is the leader instance. Running admin creation..."
    RUN_COMMAND=true
  else
    echo "This is not the leader. Skipping admin creation."
  fi
fi

if [ "$RUN_COMMAND" = "true" ]; then
  source /var/app/venv/bin/activate
  
  cd /var/app/current/
  
  python3 manage.py create_admin --role=owner
  
  echo "Admin creation script finished."
fi