#!/bin/bash

remotes=$(git remote show)
files=$(ls mac)

if [[ $files = *launch* ]]
then
    echo "launch does exist"
    echo $files
fi

if [[ $remotes = *upstream* ]]
then
    echo "Upstream already exists"
else
    echo "Adding upstream"
    git remote add upstream https://github.com/zite69/shop-cms.git
fi

if [[ -d venv ]]
then
    echo "venv already exists"
else
    echo "creating venv"
    python3.12 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.dev.txt
    python manage.py migrate
    python manage.py runscript createsu
fi
