from setuptools import setup, find_packages
setup(
    name = "TP-Link Omada Python Client",
    packages = find_packages(),
	install_requires = [
		'aiohttp>=3.8.1',
		'requests>=2.28.1',
	],
)