# CampusCart – College Stationery & Printing Management System

A Flask-based mini-project for online stationery ordering and prepaid print-and-collect services.

## Features
- Student/faculty registration and login with password hashing
- Stationery catalogue, search, cart, stock checks and order tracking
- Print & Collect: PDF, DOC, DOCX, JPG/JPEG and PNG uploads
- Printing options: black & white/colour, single/double-sided, page range, multiple copies
- Configurable starter pricing in `calculate_print_price()` in `app.py`
- Payment: local DEMO mode works immediately; Razorpay test/live integration is available when credentials are configured
- Admin dashboard, inventory updates, print queue, status updates and CSV export
- pandas/NumPy/Matplotlib analytics script
- Sample stationery products and a default admin account are seeded automatically

## Requirements
- Python 3.10+
- Windows, macOS or Linux
- Optional for PDF page counting: PyMuPDF (included in requirements)
- Optional for real payment: Razorpay account and API keys
- Optional for DOC/DOCX conversion: LibreOffice installed on the server (the starter app accepts the files and staff can download/open them in the shop's office software)

## Quick start (Windows PowerShell)
```powershell
cd CampusCart
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```
Open http://127.0.0.1:5000

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Default admin login
- Email: `admin@campuscart.local`
- Password: `Admin@12345`

Change these in `.env` before sharing or deploying. This account is for local demonstration only.

## Payment modes
### DEMO (default)
`PAYMENT_MODE=DEMO` allows the app to run without external keys. Clicking Complete demo payment marks the print job as paid for demonstration. **No real money is charged. Do not describe this as a real online payment.**

### Razorpay test mode
1. Create a Razorpay account and obtain test Key ID and Key Secret.
2. Put them in `.env`:
   ```
   PAYMENT_MODE=RAZORPAY
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxx
   RAZORPAY_KEY_SECRET=your_test_secret
   ```
3. Restart the Flask server. Use test credentials and test payment methods only.
4. For deployment, use HTTPS, secure environment variables and configure gateway webhooks/verification according to the current Razorpay documentation.

## Pricing
Starter example rates in `app.py`:
- B&W single-sided: ₹2 per printed page
- B&W double-sided: ₹3 per physical sheet
- Colour single-sided: ₹10 per printed page
- Colour double-sided: ₹15 per physical sheet

These are sample values only. Confirm actual tuck-shop prices with the shopkeeper before demonstration. Rates are stored in code in this starter version and can be moved to an admin pricing table later.

For DOC/DOCX and image uploads the initial page count is treated as one page; staff must confirm final layout before printing. PDF page count is detected automatically. The current starter app uses conservative upload validation and is intended for local academic demonstration, not public production deployment without further security review.

## Main routes
- `/` Home
- `/register`, `/login`
- `/stationery`, `/cart`
- `/printing`
- `/dashboard`, `/orders`
- `/admin` Admin dashboard
- `/admin/products` Inventory
- `/admin/orders` Order and print queue management
- `/admin/reports` Reports and CSV export
- `/health` Health check

## Run tests
```powershell
python -m unittest discover -s tests
```

## Analytics
1. Sign in as admin.
2. Open Admin > Reports > Export CSV.
3. Run:
   ```powershell
   python reports/analyze_sales.py campuscart_report.csv
   ```

## Important limitations / next production steps
- Stationery orders are currently pay-at-counter; printing is prepaid online as requested.
- DEMO payment is simulated, not a real charge.
- Add CSRF protection, rate limiting, production-grade file content inspection/antivirus scanning, secure deployment configuration, gateway webhooks, refunds and document retention automation before real public use.
- Configure a production WSGI server and HTTPS; do not use Flask debug mode in production.
- For real tuck-shop operation, verify printer workflow, actual paper sizes, pricing, page counts and refund rules with staff.

## Academic mapping
The code demonstrates Python fundamentals, control flow, functions, data structures, file handling, exceptions, JSON/CSV, OOP/database models, modular organization, NumPy, pandas and Matplotlib. Some syllabus concepts that do not naturally belong in a commerce workflow should be explained through small supplementary demonstrations during the viva rather than forced into production logic.
