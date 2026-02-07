from setuptools import setup, find_packages

setup(
    name="obiwork_core",
    version="0.1.0",
    description="OBIWORK: Institutional Grade Trading Bot for Backpack Exchange",
    author="OBIWORK Labs",
    packages=find_packages(),
    install_requires=[
        "requests",
        "python-dotenv",
        "pandas",
        "cryptography",
    ],
    entry_points={
        'console_scripts': [
            'obi-farmer=tools.volume_farmer:main',
        ],
    },
    python_requires='>=3.8',
)
