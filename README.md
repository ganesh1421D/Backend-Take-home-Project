# PubMed Industry Affiliation Filter

A Python command-line tool to search PubMed and filter articles based on author affiliations with pharmaceutical or biotech companies. This tool helps researchers and analysts identify industry-sponsored research in the biomedical literature.

## Features

- 🔍 Advanced PubMed search using NCBI E-utilities API with full query syntax support
- 🏢 Intelligent filtering of industry affiliations using comprehensive keyword matching
- 📊 Export results to well-structured CSV files
- 🚀 Command-line interface with multiple configuration options
- 📅 Date range filtering for targeted searches
- 🔄 Support for pagination of results
- 🐍 Pure Python implementation with minimal dependencies
- 📝 Detailed logging and debug output options

# 🚀 Getting Started

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## 🛠 Installation Methods

### Method 1: Using pip (Recommended for Most Users)

1. **Clone the repository**:
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/pubmed-filter.git
   
   # Navigate to the project directory
   cd pubmed-filter
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

### Method 2: Using Poetry (For Development)

1. **Install Poetry** (if not already installed):
   ```bash
   # Install Poetry
   pip install poetry
   ```

2. **Clone and set up the project**:
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/pubmed-filter.git
   cd pubmed-filter
   
   # Install dependencies
   poetry install
   ```

## ⚙️ Configuration

1. **Create a `.env` file** in the project root with your NCBI credentials:
   ```bash
   # Required: Your email address for NCBI
   NCBI_EMAIL=your.email@example.com
   
   # Optional: NCBI API key (recommended for frequent or large queries)
   NCBI_API_KEY=your_ncbi_api_key_here
   ```

2. **Get an NCBI API key** (optional but recommended):
   - Go to [NCBI Account Settings](https://www.ncbi.nlm.nih.gov/account/settings/)
   - Scroll down to the "API Key Management" section
   - Click "Create an API Key"
   - Copy the key to your `.env` file

## 🔍 Verifying Your Installation

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Verify installation**:
   ```bash
   python -c "import requests; print('Required packages are installed')"
   ```

3. **Test the installation**:
   ```bash
   python pubmed_industry_filter.py --help
   ```
   You should see the help message with available commands.

## 📦 Project Structure

```
pubmed-filter/
├── pubmed_industry_filter.py  # Main script
├── requirements.txt           # Python dependencies
├── README.md                 # This file
├── .env.example              # Example environment configuration
└── examples/                 # Example scripts and configurations
```

### Dependencies

Core dependencies (automatically installed with the package):
- `requests` - For HTTP requests to NCBI API
- `python-dotenv` - For loading environment variables
- `tqdm` - For progress bars

Development dependencies:
- `pytest` - For running tests
- `black` - For code formatting
- `mypy` - For static type checking

## 🎯 Quick Start

After installation, you can immediately start searching PubMed:

```bash
# Basic search
python pubmed_industry_filter.py "cancer treatment"

# Search with more results
python pubmed_industry_filter.py "diabetes" -n 50

# Save to a custom file
python pubmed_industry_filter.py "alzheimer" -o results.csv
```

## 🛠 Advanced Usage

### Basic Search

Search for papers about a specific topic:

```bash
python pubmed_industry_filter.py "cancer treatment"
```

### Advanced Search Examples

Search with field tags and date range:
```bash
python pubmed_industry_filter.py "cancer[Title/Abstract] AND 2020:2023[dp]" -n 50
```

Search with specific date range:
```bash
python pubmed_industry_filter.py "diabetes" --mindate 2023 --maxdate 2024
```

Save results to a custom file:
```bash
python pubmed_industry_filter.py "alzheimer" -o alzheimer_results.csv
```

### Command-line Options

```
usage: pubmed_industry_filter.py [-h] [-n MAX_RESULTS] [-o OUTPUT] [--no-file] [-d] [query]

Search PubMed for articles with industry affiliations.

positional arguments:
  query                 Search query (supports PubMed syntax)

options:
  -h, --help            Show this help message and exit
  -n, --max-results N   Maximum number of results (default: 20, max: 100,000)
  -o, --output FILE     Output CSV file (default: pubmed_industry_results.csv)
  --no-file             Print results to console instead of file
  -d, --debug           Enable debug output
  --mindate DATE        Minimum publication date (YYYY, YYYY/MM, or YYYY/MM/DD)
  --maxdate DATE        Maximum publication date (YYYY, YYYY/MM, or YYYY/MM/DD)
  --api-key KEY         NCBI API key for higher rate limits
```

### Search Syntax

The tool supports the full PubMed search syntax, including:

- **Field tags**: `cancer[Title/Abstract]`, `smith[Author]`
- **Boolean operators**: `AND`, `OR`, `NOT`
- **Date ranges**: `2020:2023[dp]`, `2023/01/01:2023/12/31[dp]`
- **MeSH terms**: `neoplasms[MeSH Terms]`
- **Wildcards**: `canc*` (matches cancer, cancers, etc.)

## 🔍 How It Works

1. **Search Phase**:
   - The tool sends your query to PubMed's E-utilities API
   - Retrieves a list of matching article IDs (PMIDs)

2. **Processing Phase**:
   - Fetches detailed information for each article
   - Analyzes author affiliations for industry connections
   - Identifies corresponding authors and their contact information

3. **Output Phase**:
   - Formats the results
   - Exports to CSV or displays in console
   - Provides summary statistics

## 📊 Output Format

The tool generates a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `PubmedID` | Unique PubMed identifier for the article |
| `Title` | Full title of the article |
| `Publication Date` | Date of publication (YYYY-MM-DD format) |
| `DOI` | Digital Object Identifier (if available) |
| `Non-academic Author(s)` | Semicolon-separated list of authors with industry affiliations |
| `Company Affiliation(s)` | Semicolon-separated list of company names from author affiliations |
| `Corresponding Author Email` | Email address(es) of corresponding authors |

### Example Output

```csv
PubmedID,Title,Publication Date,DOI,Non-academic Author(s),Company Affiliation(s),Corresponding Author Email
12345678,Novel cancer treatment,2023-06-15,10.1234/example,John Smith; Jane Doe;Pfizer Inc; Novartis,john.smith@example.com
```

## 🚨 Troubleshooting

### Common Issues

1. **API Rate Limits**
   - **Symptom**: `HTTP 429 Too Many Requests` or `HTTP 400 Bad Request`
   - **Solution**: 
     - Add your API key using `--api-key` or in the `.env` file
     - Reduce the number of results requested with `-n`
     - Add delays between requests (implemented by default)

2. **No Results Found**
   - **Check**: 
     - Your search query syntax is correct
     - The date range includes publications
     - There are no typos in field tags

3. **Authentication Errors**
   - Ensure your NCBI email is correctly set in the `.env` file
   - Verify your API key is valid (if using one)

### Debugging

Enable debug mode for detailed output:
```bash
python pubmed_industry_filter.py "your query" -d
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Running Tests

```bash
pytest tests/
```

### Code Style

We use `black` for code formatting:
```bash
black .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Resources

- [NCBI E-utilities Documentation](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
- [PubMed Search Field Descriptions](https://pubmed.ncbi.nlm.nih.gov/advanced/)
- [PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/)

## 🙏 Acknowledgments

- NCBI for providing the PubMed database and API
- The Python community for excellent libraries and tools
- All contributors who helped improve this project
- pandas
- tqdm
- python-dotenv
- requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/) for providing the PubMed API
- [BioPython](https://biopython.org/) for simplifying interaction with NCBI's services
