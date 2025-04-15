SHELL = /bin/bash
default:

clean:
	rm -f requirements*.txt
	find . -path "*__pycache__" | xargs rm -rf
	find . -path "*egg-info"    | xargs rm -rf

release:
	@git tag -a "release-v$(RELEASE_VERSION)" -m "Release v$(RELEASE_VERSION)"
	@git push origin "release-v$(RELEASE_VERSION)"
