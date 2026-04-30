# Source API keys from ~/.api_keys
if [ -f ~/.api_keys ]; then
    set -a
    source ~/.api_keys
    set +a
fi
