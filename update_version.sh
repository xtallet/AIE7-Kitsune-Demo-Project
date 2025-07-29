#!/bin/bash

# Script to update version in pyproject.toml and create git tag

if [ -z "$1" ]; then
  echo "Error: version parameter is required. Usage: ./update_version.sh X.Y.Z"
  exit 1
fi

version=$1
echo "Updating version to $version"
sed -i "s/^version = \".*\"/version = \"$version\"/" pyproject.toml

sed -i "s/^version: \".*\"/version: \"$version\"/" helm/submission-intake/Chart.yaml

git add pyproject.toml
git commit -m "chore: bump version to $version"

echo "Pushing commit to repository..."
git push origin HEAD
if [ $? -ne 0 ]; then
  echo "Error: Failed to push commit to repository. Aborting."
  exit 1
fi

echo "Creating git tag v$version..."
git tag -a v$version -m "Version $version"

echo "Pushing tag to repository..."
git push origin v$version
if [ $? -ne 0 ]; then
  echo "Error: Failed to push tag to repository. Aborting."
  exit 1
fi

echo "✅ Version updated to $version and tag v$version pushed successfully"
