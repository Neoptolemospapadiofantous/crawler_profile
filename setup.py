"""
Profile Automation System setup configuration.
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="profile-automation-system",
    version="1.0.0",
    author="Your Name",
    author_email="neoptolemos.papadiofantous@gmail.com",
    description="A modular system for automated profile management and web-based task execution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/profile-automation-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "gui": [
            # tkinter is built-in, but could add other GUI frameworks here
        ],
    },
    entry_points={
        "console_scripts": [
            "profile-automation=src.main:main",
            "pa-cli=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
    zip_safe=False,
    keywords="automation, web-scraping, selenium, profiles, anti-detection",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/profile-automation-system/issues",
        "Source": "https://github.com/yourusername/profile-automation-system",
        "Documentation": "https://github.com/yourusername/profile-automation-system/docs",
    },
)