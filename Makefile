python-installer:
	python setup.py bdist_wininst

clean:
	python -c "import shutil; shutil.rmtree('build'); shutil.rmtree('dist')"
