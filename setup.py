from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="integrador-financeiro",
    version="1.0.0",
    author="Seu Nome",
    author_email="seu.email@example.com",
    description="Consolidador automático de planilhas financeiras com validação de integridade",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seu-usuario/integrador-financeiro",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "openpyxl>=3.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "pylint>=2.17",
            "mypy>=1.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "integrador=main:main",
        ],
    },
)
