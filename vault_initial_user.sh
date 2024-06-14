#!/bin/bash

export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN=""
YOUR_CHOSEN_USERNAME=""
YOUR_CHOSEN_PASSWORD="" # ENTER YOUR PASSWORD HERE, OR ENVIRONMENT VARIABLE WHERE THE PASSWORD IS LOCATED
YOUR_EMAIL_HERE=""
YOUR_GITHUB_TOKEN_HERE=""


echo $VAULT_TOKEN | vault login -

vault auth enable userpass

vault policy write github - << EOF
path "secret/*" {
    capabilities = ["read", "list", "create", "update"]
}
EOF



vault write auth/userpass/users/"${YOUR_CHOSEN_USERNAME}" password="${YOUR_CHOSEN_PASSWORD}" policies=github

vault secrets enable -path=secret/ kv

vault kv put secret/github/email key="${YOUR_EMAIL_HERE}"
echo $VAULT_TOKEN
vault kv put secret/github/GITHUB_TOKEN key="${YOUR_GITHUB_TOKEN_HERE}"

unset VAULT_TOKEN

vault login -method=userpass username="${YOUR_CHOSEN_USERNAME}"