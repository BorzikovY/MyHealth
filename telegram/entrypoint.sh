#!/bin/bash

set -e

host="my-health.site"
port="443"
cmd="$@"

>&2 echo "Check server connection access"

until curl https://"$host":"$port"; do
  >&2 echo "server is starting - sleeping"
  sleep 1
done

>&2 echo "Server is ready to accept connections"

exec $cmd
