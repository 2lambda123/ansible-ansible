#!/usr/bin/env bash

set -eux

export ANSIBLE_INSTALLED_CONTENT_ROOTS=$PWD/collection_root_user,$PWD/collection_root_sys
export ANSIBLE_GATHERING=explicit
export ANSIBLE_GATHER_SUBSET=minimal

# temporary hack to keep this test from running on Python 2.6 in CI
if ansible-playbook -i ../../inventory pythoncheck.yml | grep UNSUPPORTEDPYTHON; then
  echo skipping test for unsupported Python version...
  exit 0
fi

ansible-playbook -i ../../inventory -i ./a.statichost.yml -v play.yml
