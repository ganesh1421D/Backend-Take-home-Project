import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import csv
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Global debug flag
DEBUG = False

def debug_print(*args, **kwargs):
    """Print debug messages if debug mode is enabled."""
    if DEBUG:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG {timestamp}]", *args, **kwargs)

# NCBI E-utilities API endpoints
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Your email (required by NCBI)
EMAIL = "dasariganesh334@gmail.com"

# Keywords to identify industry affiliations
INDUSTRY_KEYWORDS = [
    'pharma', 'pharmaceutical', 'biotech', 'biotechnology',
    'inc', 'ltd', 'llc', 'plc', 'corporation', 'company',
    'gmbh', 'ag', 'sas', 'sarl', 'labs', 'research', 'healthcare',
    'pfizer', 'novartis', 'roche', 'merck', 'johnson & johnson',
    'gsk', 'glaxosmithkline', 'sanofi', 'astrazeneca', 'eli lilly'
]

# Keywords that typically indicate academic affiliations
ACADEMIC_KEYWORDS = [
    'university', 'college', 'institute', 'academy', 'school',
    'hospital', 'clinic', 'medical center', 'research center',
    'universit\xe9', 'universita', 'universidad', '\u682a\u5f0f\u4f1a\u793e'  # Non-English variants
]

def make_api_request(url: str, params: Dict) -> str:
    """Make an HTTP request to the NCBI API."""
    # Encode parameters properly
    encoded_params = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{url}?{encoded_params}"
    
    if DEBUG:
        debug_print(f"Making request to: {full_url}")
    
    try:
        # Add a user-agent header to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        req = urllib.request.Request(full_url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        debug_print(f"HTTP Error {e.code}: {error_msg}")
        raise Exception(f"HTTP Error {e.code}: {e.reason}")
    except Exception as e:
        debug_print(f"Error making request: {str(e)}")
        raise

def search_pubmed(query: str, max_results: int = 10, **kwargs) -> List[str]:
    """
    Search PubMed and return a list of article IDs.
    
    Args:
        query: PubMed search query string. Supports PubMed's query syntax including:
              - Field tags: 'cancer[Title/Abstract]', 'smith[Author]'
              - Boolean operators: AND, OR, NOT
              - Date ranges: '2020:2023[dp]', '2023/01/01:2023/12/31[dp]'
              - MeSH terms: 'neoplasms[MeSH]'
        max_results: Maximum number of results to return (default: 10, max: 100,000)
        **kwargs: Additional parameters for the PubMed API
            - mindate: Minimum publication date (YYYY/MM/DD, YYYY, or YYYY/MM)
            - maxdate: Maximum publication date (YYYY/MM/DD, YYYY, or YYYY/MM)
            - retstart: Index of the first result to return (for pagination)
            
    Returns:
        List of PubMed article IDs matching the search criteria
    """
    debug_print(f"Searching PubMed for: {query}")
    debug_print(f"Max results requested: {max_results}")
    
    # Basic parameters
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': str(min(int(max_results), 100000)),  # PubMed's max limit
        'retmode': 'json',
        'email': EMAIL,
        'tool': 'PubMedIndustryFilter',
        'sort': 'relevance',
        'api_key': kwargs.get('api_key'),  # Optional API key for higher rate limits
        'datetype': 'pdat',  # Search by publication date
        'retstart': str(kwargs.get('retstart', 0))  # For pagination
    }
    
    # Add date range if provided
    if 'mindate' in kwargs:
        params['mindate'] = kwargs['mindate']
    if 'maxdate' in kwargs:
        params['maxdate'] = kwargs['maxdate']
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = make_api_request(ESEARCH_URL, params)
        data = json.loads(response)
        
        # Check for errors in response
        if 'error' in data:
            raise Exception(f"PubMed API error: {data['error']}")
            
        return data.get('esearchresult', {}).get('idlist', [])
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse PubMed response: {str(e)}")
    except Exception as e:
        raise Exception(f"Error searching PubMed: {str(e)}")

def parse_author(author_elem) -> Dict:
    """Parse author information from XML."""
    last_name = author_elem.find('LastName')
    fore_name = author_elem.find('ForeName')
    
    if last_name is None or fore_name is None:
        return None
    
    # Get affiliation info
    affiliation_info = author_elem.find('AffiliationInfo')
    affiliation = affiliation_info.find('Affiliation').text if affiliation_info is not None else ""
    
    # Check if corresponding author
    is_corresponding = author_elem.get('ValidYN', 'N') == 'Y' or 'corresponding' in (affiliation or '').lower()
    
    # Try to extract email
    email = None
    if affiliation:
        # Simple email regex pattern
        import re
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', affiliation)
        if email_match:
            email = email_match.group(0)
    
    return {
        'name': f"{fore_name.text} {last_name.text}",
        'affiliation': affiliation,
        'email': email,
        'is_corresponding': is_corresponding
    }

def is_industry_affiliation(affiliation: str):
    """Check if an affiliation is likely from industry."""
    if not affiliation:
        debug_print("  No affiliation text")
        return False
        
    # Convert to lowercase for case-insensitive matching
    affil_lower = affiliation.lower()
    
    # Debug output
    debug_print(f"  Checking affiliation: {affiliation}")
    
    # First check for academic keywords
    for keyword in ACADEMIC_KEYWORDS:
        if keyword in affil_lower:
            debug_print(f"    Matched academic keyword: {keyword}")
            return False
    
    # Then check for industry keywords
    for keyword in INDUSTRY_KEYWORDS:
        if keyword in affil_lower:
            debug_print(f"    Matched industry keyword: {keyword}")
            return True
    
    debug_print("    No industry keywords matched")
    return False

def get_article_details(article_id: str) -> Optional[Dict]:
    debug_print(f"\nFetching details for article ID: {article_id}")
    """Get detailed information for a single article."""
    params = {
        'db': 'pubmed',
        'id': article_id,
        'retmode': 'xml',
        'email': EMAIL,
        'tool': 'PubMedIndustryFilter'
    }
    
    try:
        response = make_api_request(EFETCH_URL, params)
        root = ET.fromstring(response)
        
        # Find the article element
        article = root.find('.//PubmedArticle')
        if article is None:
            return None
        
        # Extract basic information
        article_data = article.find('.//Article')
        if article_data is None:
            return None
        
        # Debug: Print all affiliations
        medline = article.find('.//MedlineCitation')
        if medline is None:
            return None
            
        affiliations = medline.findall('.//Affiliation')
        if affiliations:
            debug_print(f"Found {len(affiliations)} affiliations for article {article_id}:")
            for i, affil in enumerate(affiliations, 1):
                affil_text = affil.text.strip() if affil.text else "No text"
                debug_print(f"  {i}. {affil_text}")
        else:
            debug_print(f"No affiliations found for article {article_id}")
        
        # Get title
        title_elem = article_data.find('.//ArticleTitle')
        title = ' '.join(title_elem.itertext()) if title_elem is not None else "No title available"
        
        # Get publication date
        pub_date = article.find('.//PubDate')
        pub_date_str = ""
        if pub_date is not None:
            year = pub_date.find('Year')
            month = pub_date.find('Month')
            day = pub_date.find('Day')
            
            date_parts = []
            if year is not None and year.text:
                date_parts.append(year.text)
                if month is not None and month.text:
                    date_parts.append(month.text)
                    if day is not None and day.text:
                        date_parts.append(day.text)
            
            pub_date_str = '-'.join(date_parts) if date_parts else "Date not available"
        
        # Process authors
        authors = []
        industry_authors = []
        corresponding_emails = set()
        
        for author_elem in article.findall('.//Author'):
            author = parse_author(author_elem)
            if author:
                authors.append(author)
                if author['is_corresponding'] and author['email']:
                    corresponding_emails.add(author['email'])
                
                # Check for industry affiliation
                if is_industry_affiliation(author['affiliation']):
                    industry_authors.append(author)
        
        # Only include papers with at least one industry author
        if not industry_authors:
            return None
        
        # Get DOI if available
        doi = ""
        article_id_list = article.findall('.//ArticleIdList/ArticleId')
        for article_id_elem in article_id_list:
            if article_id_elem.get('IdType') == 'doi':
                doi = article_id_elem.text
                break
        
        return {
            'pubmed_id': article_id,
            'title': title,
            'publication_date': pub_date_str,
            'doi': doi,
            'all_authors': authors,
            'industry_authors': industry_authors,
            'corresponding_emails': list(corresponding_emails)
        }
        
    except Exception as e:
        print(f"Error processing article {article_id}: {e}")
        return None

def save_to_csv(papers: List[Dict], filename: str):
    """Save the results to a CSV file."""
    if not papers:
        debug_print("No papers to save to CSV")
        return
    
    debug_print(f"Saving {len(papers)} papers to {filename}")
    
    # Define CSV columns
    fieldnames = [
        'PubmedID',
        'Title',
        'Publication Date',
        'DOI',
        'Non-academic Author(s)',
        'Company Affiliation(s)',
        'Corresponding Author Email'
    ]
    
    # Prepare data for CSV
    rows = []
    for paper in papers:
        # Format industry authors and their affiliations
        industry_authors = []
        affiliations = set()
        
        for author in paper['industry_authors']:
            industry_authors.append(author['name'])
            if author['affiliation']:
                affiliations.add(author['affiliation'])
        
        # Create a row for the CSV
        row = {
            'PubmedID': paper['pubmed_id'],
            'Title': paper['title'],
            'Publication Date': paper['publication_date'],
            'DOI': paper['doi'],
            'Non-academic Author(s)': '; '.join(industry_authors),
            'Company Affiliation(s)': '; '.join(affiliations),
            'Corresponding Author Email': '; '.join(paper['corresponding_emails'])
        }
        rows.append(row)
    
    # Write to CSV
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"\nResults saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def is_valid_date(date_str):
    """Validate date format (YYYY, YYYY/MM, or YYYY/MM/DD)."""
    import re
    return bool(re.match(r'^\d{4}(/\d{1,2}(/\d{1,2})?)?$', date_str))

def show_help():
    """Display help information."""
    help_text = """
PubMed Industry Affiliation Filter
---------------------------------

USAGE:
  python pubmed_industry_filter.py "search query" [options]

SEARCH SYNTAX:
  Supports all PubMed query syntax including:
  - Field tags: "cancer[Title/Abstract]", "smith[Author]"
  - Boolean operators: AND, OR, NOT
  - Date ranges: "2020:2023[dp]", "2023/01/01:2023/12/31[dp]"
  - MeSH terms: "neoplasms[MeSH]"

OPTIONS:
  -h, --help      Show this help message and exit
  -n, --max-results N  Maximum number of results (default: 20, max: 100,000)
  -o, --output FILE   Output CSV file (default: pubmed_industry_results.csv)
  --no-file       Print to console instead of file
  -d, --debug     Enable debug output
  --api-key KEY   NCBI API key for higher rate limits

DATE FILTERING:
  --mindate DATE  Minimum publication date (YYYY, YYYY/MM, or YYYY/MM/DD)
  --maxdate DATE  Maximum publication date (YYYY, YYYY/MM, or YYYY/MM/DD)

EXAMPLES:
  # Basic search
  python pubmed_industry_filter.py "cancer treatment"
  
  # Search with field tags and date range
  python pubmed_industry_filter.py "cancer[Title/Abstract] AND 2020:2023[dp]"
  
  # Limit results and save to custom file
  python pubmed_industry_filter.py "diabetes" -n 100 -o diabetes_results.csv
  
  # Search with date range filters
  python pubmed_industry_filter.py "alzheimer" --mindate 2020 --maxdate 2023
  
  # Print to console with debug output
  python pubmed_industry_filter.py "covid" --no-file -d
"""
    print(help_text)
    sys.exit(0)

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    # First check for help flag
    if '-h' in sys.argv or '--help' in sys.argv:
        show_help()
    
    # Create the parser
    parser = argparse.ArgumentParser(add_help=False)
    
    # Add arguments
    parser.add_argument('query', nargs='?', default=None, 
                      help='PubMed search query (supports PubMed syntax)')
    parser.add_argument('-n', '--max-results', type=int, default=20,
                      help='Maximum number of results to return (default: 20)')
    parser.add_argument('-o', '--output', default='pubmed_industry_results.csv',
                      help='Output CSV file (default: pubmed_industry_results.csv)')
    parser.add_argument('--no-file', action='store_true',
                      help='Print results to console instead of file')
    parser.add_argument('-d', '--debug', action='store_true',
                      help='Enable debug output')
    
    # Add date range options
    date_group = parser.add_argument_group('date filtering')
    date_group.add_argument('--mindate', 
                          help='Minimum publication date (YYYY/MM/DD, YYYY, or YYYY/MM)')
    date_group.add_argument('--maxdate', 
                          help='Maximum publication date (YYYY/MM/DD, YYYY, or YYYY/MM)')
    
    # Add API key option
    parser.add_argument('--api-key', help='NCBI API key for higher rate limits')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no query provided but not asking for help, show help
    if args.query is None and not any(arg in sys.argv for arg in ['-h', '--help']):
        show_help()
    
    # Validate date formats if provided
    if args.mindate and not is_valid_date(args.mindate):
        print(f"Error: Invalid mindate format. Use YYYY, YYYY/MM, or YYYY/MM/DD")
        sys.exit(1)
    if args.maxdate and not is_valid_date(args.maxdate):
        print(f"Error: Invalid maxdate format. Use YYYY, YYYY/MM, or YYYY/MM/DD")
        sys.exit(1)
    
    return args
    
    return parser.parse_args()

def print_results(papers: list, output_file: str = None):
    """Print or save results based on parameters."""
    if not papers:
        print("\nNo papers with industry affiliations found.")
        return
    
    if output_file:
        save_to_csv(papers, output_file)
        print(f"\nFound {len(papers)} papers with industry affiliations. Results saved to {output_file}")
    else:
        # Print to console
        print("\n" + "="*80)
        print(f"FOUND {len(papers)} PAPERS WITH INDUSTRY AFFILIATIONS")
        print("="*80)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   PMID: {paper['pubmed_id']}")
            print(f"   Published: {paper['publication_date']}")
            print(f"   DOI: {paper.get('doi', 'N/A')}")
            print("   Industry Authors:")
            for author in paper.get('industry_authors', []):
                email = f" ({author['email']})" if author.get('email') else ""
                print(f"     - {author['name']}{email}")
                if author.get('affiliation'):
                    print(f"       {author['affiliation']}")
            print("-" * 80)

def main():
    """
    Main function to run the PubMed search and filter.
    Handles command-line arguments, executes the search, and manages output.
    """
    try:
        args = parse_arguments()
        
        # Set debug mode
        global DEBUG
        DEBUG = args.debug
        
        query = args.query
        max_results = args.max_results
        output_file = None if args.no_file else args.output
        
        print(f"Searching PubMed for: {query}")
        if args.mindate or args.maxdate:
            date_range = []
            if args.mindate:
                date_range.append(f"from {args.mindate}")
            if args.maxdate:
                date_range.append(f"to {args.maxdate}")
            print(f"Date range: {' '.join(date_range)}")
        print(f"Processing up to {max_results} results...")
        print("-" * 80)
        
        # Prepare search parameters
        search_params = {
            'max_results': max_results,
            'api_key': args.api_key
        }
        
        # Add date filters if provided
        if args.mindate:
            search_params['mindate'] = args.mindate
        if args.maxdate:
            search_params['maxdate'] = args.maxdate
        
        # Search PubMed
        article_ids = search_pubmed(query, **search_params)
        
        if not article_ids:
            print("No articles found matching your query.")
            return
            
        # Get article details
        papers = []
        for i, article_id in enumerate(article_ids, 1):
            try:
                if DEBUG:
                    print(f"\rProcessing article {i}/{len(article_ids)}...", end="")
                paper = get_article_details(article_id)
                if paper:
                    papers.append(paper)
                    if DEBUG:
                        print(f"\rFound {len(papers)} articles with industry affiliations...", end="")
            except Exception as e:
                if DEBUG:
                    print(f"\nError processing article {article_id}: {e}")
        
        if DEBUG:
            print()  # New line after progress indicator
            
        # Print or save results
        print_results(papers, output_file)
        
        # Show summary
        print(f"\nSearch complete. Found {len(papers)} articles with industry affiliations.")
        if not args.no_file and output_file:
            print(f"Results saved to: {output_file}")
        
    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
