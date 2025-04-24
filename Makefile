SHELL = /bin/bash
default:

clean:
	find . -path ".pdm-build" | xargs rm -rf
	find . -path "dist/*" | xargs rm -rf
	find . -path "*__pycache__" | xargs rm -rf
	find . -path "*egg-info"    | xargs rm -rf
	find . -path "*_version.py" | xargs rm -rf