#!/bin/bash
set -e

# Start the gptme server with specified host and port (11130)
exec gptme-server serve --host 0.0.0.0 --port 11130
