#!/bin/bash
rm ./dist/*.whl
python setup.py sdist bdist_wheel
twine upload dist/*.whl