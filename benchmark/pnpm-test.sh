#!/bin/bash

# exit when any command fails
set -e

# Create symlinks if they don't exist
[ ! -e node_modules ] && ln -s /pnpm-install/node_modules .
[ ! -e pnpm-lock.yaml ] && ln -s /pnpm-install/pnpm-lock.yaml .


sed -i 's/\bxtest(/test(/g' *.spec.js
pnpm run test

