# AI Agent Instructions for FMH_Aud2Ins_GraphQl_S3

## Project Overview
This project interfaces with a GraphQL API to fetch and process call transcription data. It's designed to work with a specific GraphQL endpoint that provides information about calls, entities, and their associated recordings stored in S3.

## Key Components

### GraphQL Data Fetching (`get.py`)
- Main entry point for fetching call transcription data
- Uses the `requests` library for GraphQL API communication
- Implements error handling and response validation
- Returns structured data including entity details and S3 recording URLs

### Data Schema
The GraphQL query retrieves the following key data points:
- Entity information (ID, name, type, location)
- Call details (ID, status, description)
- Property details (rent range, security deposit)
- Contact information (owner name, email)
- Facility information (beds, warden status, visitor policy)
- S3 recording URLs and creation timestamps

## Development Patterns

### Date Handling
- Dates are expected in ISO 8601 format (e.g., "2025-10-01T18:30:00.000Z")
- Default date range spans a month
- Time zones should be explicitly specified in the date strings

### Error Handling
The codebase follows a pattern of:
1. Wrapping API calls in try-except blocks
2. Returning empty lists on failures
3. Providing descriptive error messages with emoji indicators:
   - ❌ for HTTP failures
   - ⚠️ for general exceptions

### Response Processing
- Responses are limited by the `limit` parameter (default: 10)
- Data is accessed using safe dictionary get() operations with defaults
- JSON responses are pretty-printed for debugging

## Integration Points
1. GraphQL Endpoint: Expected to be accessible via HTTPS (e.g., ngrok tunnel)
2. AWS S3: Recording files are referenced via S3 URLs in the response

## Testing
To test the functionality:
1. Run `get.py` directly
2. Verify JSON output is properly formatted
3. Check S3 URLs are valid and accessible

## Common Commands
```python
# Basic usage with default parameters
python get.py

# Custom date range example
from get import fetch_call_data_transcribe
result = fetch_call_data_transcribe(
    "https://your-endpoint/graphql",
    from_date="2025-10-01T00:00:00.000Z",
    to_date="2025-10-31T23:59:59.999Z",
    limit=20
)
```