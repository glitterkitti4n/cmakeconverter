python setup.py sdist bdist_wheel

rem test uploading
twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

rem release uploading
rem twine upload dist/*

@pause