#!/bin/bash

# Check for required environment variables
required_vars=("ORG_NAME" "PROJECT_NAME" "SOLUTION_NAME" "RELEASE_VERSION" "RELEASE_QUERY" "PAT" "GPT_API_KEY" "SOFTWARE_SUMMARY" "DESIRED_WORK_ITEM_TYPES" "OUTPUT_FOLDER")

for var in "${required_vars[@]}"
do
  if [ -z "${!var}" ]; then
    echo "Error: $var is not set."
    exit 1
  fi
done

# Create .env file
cat <<EOF > .env
ORG_NAME=$ORG_NAME
PROJECT_NAME=$PROJECT_NAME
SOLUTION_NAME=$SOLUTION_NAME
RELEASE_VERSION=$RELEASE_VERSION
RELEASE_QUERY=$RELEASE_QUERY
PAT=$PAT
GPT_API_KEY=$GPT_API_KEY
SOFTWARE_SUMMARY=$SOFTWARE_SUMMARY
DESIRED_WORK_ITEM_TYPES=$DESIRED_WORK_ITEM_TYPES
OUTPUT_FOLDER=$OUTPUT_FOLDER
EOF

echo ".env file created successfully."