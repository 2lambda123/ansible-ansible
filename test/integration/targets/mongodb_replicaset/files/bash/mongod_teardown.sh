#!/bin/sh

set -e;
set -u;

killall mongod || true
rm -rf /home/tests/mongodb*;
rm -f /tmp/mongodb*.sock;
