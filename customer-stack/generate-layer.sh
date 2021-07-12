#!/bin/sh

mkdir layer

mkdir -p layer/snowflake-connector-python/python/lib/python3.7/site-packages
python3.7 -m venv layer/.temp
source layer/.temp/bin/activate
pip3 install snowflake-connector-python
deactivate
mv layer/.temp/lib/python3.7/site-packages/* layer/snowflake-connector-python/python/lib/python3.7/site-packages
rm -rf layer/.temp
