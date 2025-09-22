"""
CDP Ninja Setup Script
Lightweight Chrome DevTools Protocol bridge for browser debugging
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
try:
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Lightweight Chrome DevTools Protocol bridge for browser debugging"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
try:
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]
except FileNotFoundError:
    requirements = [
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "websocket-client>=1.7.0",
        "psutil>=5.9.6",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0"
    ]

setup(
    name="cdp-ninja",
    version="1.0.1",
    author="CDP Ninja Contributors",
    author_email="dev@example.com",
    description="🥷 Lightweight Chrome DevTools Protocol bridge for browser debugging and security testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/travofoz/cdp-ninja",
    project_urls={
        "Bug Reports": "https://github.com/travofoz/cdp-ninja/issues",
        "Source": "https://github.com/travofoz/cdp-ninja",
        "Documentation": "https://github.com/travofoz/cdp-ninja/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
        ],
        "windows": [
            "pywin32>=306;sys_platform=='win32'",
        ],
    },
    entry_points={
        "console_scripts": [
            "cdp-ninja=api.server:main",
            "cdp-ninja-setup=setup.install:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "*.md",
            "*.txt",
            "*.json",
            "*.ps1",
            "setup/*.ps1",
            "setup/*.sh",
            "agent/*.md",
            "examples/*.py"
        ],
    },
    zip_safe=False,
    keywords=[
        "chrome",
        "devtools",
        "debugging",
        "browser",
        "automation",
        "cdp",
        "testing",
        "performance",
        "network",
        "console"
    ],
)