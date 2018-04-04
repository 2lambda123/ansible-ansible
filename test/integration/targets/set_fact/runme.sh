#!/usr/bin/env bash

set -eux

MYTMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
trap 'rm -rf "${MYTMPDIR}"' EXIT

# ensure we can incrementally set fact via loop
ansible-playbook -i ../../inventory incremental.yml

# ensure we dont have spurious warnings do to clean_facts
ansible-playbook -i ../../inventory nowarn_clean_facts.yml | grep '[WARNING]: Removed restricted key from module data: ansible_ssh_common_args' && exit 1

# test cached feature
export ANSIBLE_CACHE_PLUGIN=jsonfile ANSIBLE_CACHE_PLUGIN_CONNECTION="${MYTMPDIR}"
ansible-playbook -i ../../inventory "$@" set_fact_cached_1.yml
ansible-playbook -i ../../inventory "$@" set_fact_cached_2.yml
ansible-playbook -i ../../inventory --flush-cache "$@" set_fact_no_cache.yml
