#!/bin/bash

WEBHOOK_PAYLOAD_URL='https://ci.guzek.uk'

log() {
	echo "INFO:  $1"
}

fail() {
	echo "FATAL: $1"
	exit 1
}

if [[ -z "$1" || ! "$1" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
	fail "Invalid repository name '$1'"
fi

APP_DIR="/data/apps/$1"
if [ -d $APP_DIR ]; then
	log "Skipping clone (directory exists)"
else
	if ! git clone git@github.com:kguzek/$1 $APP_DIR; then
	       fail "Failed to clone repository"
	fi
	log "Cloned repository successfully"
fi

if ! git config --global --get-all safe.directory | grep $APP_DIR >/dev/null; then
	git config --global --add safe.directory $APP_DIR
	log "Added $APP_DIR to the list of safe git directories"
fi
# sudo chown -R konrad:gad $APP_DIR
chmod -R g+rw $APP_DIR

read -rp "INPUT: Post-push deploy command: " DEPLOY_COMMAND
SETTINGS_FILE='/data/apps/Git-Auto-Deploy/config.json'
SECRET_TOKEN=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 20 | head -n 1)
NEW_REPO_ENTRY="{
  \"url\": \"https://github.com/kguzek/$1.git\",
  \"branch\": \"main\",
  \"path\": \"$APP_DIR\",
  \"deploy\": $(jq -n --arg var "$DEPLOY_COMMAND" '$var'),
  \"secret-token\": \"$SECRET_TOKEN\"
}"
TEMP_SETTINGS_FILE="$SETTINGS_FILE.new"
SETTINGS_WITHOUT_REPOSITORIES=$(sed -n '1,/"repositories":/{\/\"repositories\":/!p}' "$SETTINGS_FILE")
PREVIOUS_REPOSITORIES=$(sed -n '/"repositories":/,$p' "$SETTINGS_FILE")
if [ -z "$PREVIOUS_REPOSITORIES" ]; then
	fail "Could not parse the repositories field."
fi
PREVIOUS_REPOSITORIES="{$PREVIOUS_REPOSITORIES"

if ! echo "$PREVIOUS_REPOSITORIES" | jq -e ".repositories | map(.path != \"$APP_DIR\") | all" >/dev/null; then
	echo "$PREVIOUS_REPOSITORIES"
	fail "This repository has already been added to the CI/CD pipeline."
fi

UPDATED_REPOSITORIES=$(echo "$PREVIOUS_REPOSITORIES" | jq ".repositories += [$NEW_REPO_ENTRY]" | sed '1d')
if [ $? -ne 0 ]; then
	echo "$PREVIOUS_REPOSITORIES"
	fail "Failed to parse settings file."
fi
echo "$SETTINGS_WITHOUT_REPOSITORIES" > "$TEMP_SETTINGS_FILE"
echo >> "$TEMP_SETTINGS_FILE"
echo "$UPDATED_REPOSITORIES" >> "$TEMP_SETTINGS_FILE"

mv "$TEMP_SETTINGS_FILE" "$SETTINGS_FILE"
log "Successfully created repository CI/CD configuration"
log "Payload URL  (for GitHub webhook): $WEBHOOK_PAYLOAD_URL"
log "Secret token (for GitHub webhook): $SECRET_TOKEN"
log "Restart the Git Auto Deploy service for configuration to take effect:"
echo "sudo systemctl restart gitautodeploy"
