# Text Sync

A web tool that fixes one of the most frustrating problems with textbook PDFs: the page numbers don't match.

When you open a textbook PDF, the cover is page 1, followed by roman numeral front matter — by the time you reach the actual content, the PDF page number is much higher than the printed page number in the book. Every time you want to navigate to a specific page, you have to do mental arithmetic.

**Text Sync solves this.** Upload your textbook PDF and receive a corrected version with a fully linked table of contents. Click any chapter or section in the PDF sidebar and jump directly to the right page — no calculations needed.

---

## How It Works

1. You upload a textbook PDF through the website
2. Text Sync extracts the first 50 pages and sends them to Google Gemini AI
3. Gemini reads the table of contents and returns all chapter titles with their printed page numbers
4. The offset between PDF page numbers and printed page numbers is calculated
5. The corrected table of contents is written directly into the PDF's metadata — every chapter and subsection with the correct hierarchy level
6. The corrected PDF is returned as a download

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| PDF parsing | PyMuPDF |
| AI | Google Gemini 2.5 Flash API |
| Hosting | AWS Elastic Beanstalk |
| Web server | Nginx + Gunicorn |

---

## Project Structure

```
textsync/
├── server.py             ← Flask server and API routes
├── find_toc.py           ← Uploads PDF to Gemini, returns TOC as JSON
├── parse_result.py       ← Parses Gemini response, calculates page offset
├── shift_page.py         ← Writes corrected TOC into PDF metadata
├── requirements.txt      ← Python dependencies
├── Procfile              ← Gunicorn startup command for AWS
├── .platform/
│   └── nginx/
│       └── conf.d/
│           ├── proxy.conf    ← Raises Nginx upload size limit to 50MB
│           └── timeout.conf  ← Extends proxy timeouts to 5 minutes
├── templates/
│   └── index.html        ← Frontend HTML
└── static/
    ├── css/
    │   └── style.css     ← Styling
    └── js/
        └── script.js     ← Upload logic, validation, progress bar
```

---

## Running Locally

**Prerequisites:**
- Python 3.9+
- A Google Gemini API key (get one free at https://aistudio.google.com)

**Setup:**
```bash
# Clone the repo
git clone https://github.com/Snehil36/textsync.git
cd textsync

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key as an environment variable
export PDF_OFFSETTER="your-gemini-api-key-here"

# Run the server
python3 server.py
```

Then open `http://127.0.0.1:5000` in any browser — Chrome, Firefox, Safari, Edge, etc.

---

## Deployment

Text Sync is deployed on **AWS Elastic Beanstalk** using a production-grade stack:

**Architecture:**
```
Internet
    ↓
AWS Application Load Balancer
    ↓
Nginx (reverse proxy on EC2)
    ↓
Gunicorn (WSGI server)
    ↓
Flask application
    ↓
Google Gemini API
```

**Key production configurations:**

- **Gunicorn** serves the Flask app with a 120 second worker timeout to handle long-running Gemini API calls
- **Nginx** is configured with a 50MB upload limit (`client_max_body_size 50M`) and 5 minute proxy timeouts to prevent large PDF uploads from being rejected
- **Gemini client** uses `api_version='v1'` and a 120 second SDK timeout to prevent network path corruption on AWS infrastructure
- **Environment variables** are stored securely using `eb setenv` — the API key is never hardcoded or committed to the repository
- **ProxyFix middleware** ensures Flask correctly reads headers forwarded through the AWS load balancer

**To deploy your own instance:**
```bash
# Install EB CLI
pip install awsebcli

# Initialize and deploy
eb init
eb create your-env-name
eb setenv PDF_OFFSETTER="your-gemini-api-key"
eb deploy
```

**Note:** HTTPS will be enabled once a custom domain is configured via AWS Route 53 and ACM (AWS Certificate Manager).

---

## Security

- File type validated by magic bytes (`%PDF`), not just filename extension
- Filename sanitized with `werkzeug.secure_filename()` — prevents path traversal attacks
- Upload size capped at 100MB at the Flask layer
- Temp files stored using UUIDs, never paths derived from user input
- All pipeline calls are direct Python functions — no subprocess, no shell injection surface
- Generic error responses — no internal details exposed to the client
- Temp files deleted immediately after each request, success or failure
- CORS disabled — same-origin requests only
- `debug=False` enforced — no interactive console exposed in the browser

---

## Future Plans

### Chrome Extension
Text Sync will also be available as a Chrome extension. Since the backend is already hosted on AWS, the extension frontend will simply point at the hosted URL — no backend changes required.

### Other Planned Improvements
- HTTPS support once a custom domain is acquired
- Async processing for large PDFs (currently synchronous, can take 30-60 seconds)
- Support for appendix pages with non-standard numbering (e.g. "A-1")
- Support for roman numeral front matter sections
- Browser extension versions for Firefox and Edge

---

## Known Limitations
- Gemini has a 1000 page PDF limit — handled by sending only the first 50 pages for TOC extraction
- Processing is synchronous — large PDFs may take up to 60 seconds
- Appendix pages with non-standard page numbers (e.g. "A-1") are detected but not currently mapped
- Requires a Google Gemini API key to run
- Currently running on HTTP — HTTPS will be enabled once a custom domain is configured

---

## Related Repository
The Python prototype used to develop and test the core logic before building the full web application:
**https://github.com/Snehil36/pdf_page_mapper**

---

## Author
Built by Snehil
