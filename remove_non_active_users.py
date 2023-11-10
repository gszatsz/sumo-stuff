import requests
from datetime import datetime, timedelta
import base64
import json

# Sumo Logic API endpoint for "prod" deployment for other deployments use https://api.<deployment>.sumologic.com/api/v1/ example: https://api.us2.sumologic.com/api/v1/
api_endpoint = "https://api.sumologic.com/api/v1/"

# Sumo Logic credentials
$AccessKey = "YourAccessKey"
$SecretKey = "YourSecretKey"

# Set the number of days for user deletion
days = 90

# Set to True for a dry run, set to False to actually delete a user
dry_run = True

# Excludes Sumo Support Account
exclude_pattern = 'sumosupport'

# Specify whether to exclude deactivated users (True or False) by default this will ignore deactivated users
exclude_deactivated = True

# Function to get users from Sumo Logic API
def get_users():
    url = api_endpoint + "users"
    auth_header = "Basic " + base64.b64encode(f"{access_key}:{secret_key}".encode()).decode()
    headers = {"Authorization": auth_header}
    response = requests.get(url, headers=headers)

    # Check for errors
    response.raise_for_status()

    # Try to decode JSON if the response has content
    if response.content:
        try:
            return response.json()["data"]
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
    else:
        print("Empty response received from the API.")

    return []

# Function to remove a user by id from Sumo Logic API
def remove_user_by_id(user_id):
    url = api_endpoint + f"users/{user_id}"
    auth_header = "Basic " + base64.b64encode(f"{access_key}:{secret_key}".encode()).decode()
    headers = {"Authorization": auth_header}
    if not dry_run:
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print(f"User with id {user_id} deleted successfully.")
        else:
            print(f"Failed to delete user with id {user_id}. Status code: {response.status_code}")
    else:
        print(f"DRY RUN: User with id {user_id} would be deleted.")

# Get current date and time
now = datetime.utcnow()

# Get users from Sumo Logic
users = get_users()

# Print information about all users
print(f"Total Users: {len(users)}")
for user in users:
    print(f"User: {user['id']} {user['email']} lastLoginTimestamp: {user['lastLoginTimestamp']}")

# Filter users based on simplified conditions
users_to_delete = [user for user in users if not (
    user["email"].lower().startswith(exclude_pattern.lower()) or
    (user["lastLoginTimestamp"] is not None and (now - datetime.strptime(user["lastLoginTimestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")).days <= days) or
    (exclude_deactivated and user["isActive"] is False) or
    'sumosupport' in user["email"].lower()
)]

# Display information and delete users
print(f"Simplified Matched: {len(users_to_delete)} users.")
for user in users_to_delete:
    last_login_timestamp = user.get('lastLoginTimestamp', None)
    if last_login_timestamp is not None:
        days_ago = (now - datetime.strptime(last_login_timestamp[:19], '%Y-%m-%dT%H:%M:%S')).days
    else:
        days_ago = None
    print(f"User: {user['id']} {user['email']} lastLoginTimestamp: {last_login_timestamp} was {days_ago} days ago.")
    remove_user_by_id(user["id"])
