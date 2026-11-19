# CAMPUSCART
## Online College Stationery & Prepaid Printing Management System

**Mini Project Report – Python Programming**

**Student Name:** __________________________  
**USN / Register Number:** __________________  
**Class / Section:** _________________________  
**Department:** _____________________________  
**Institution:** _____________________________  
**Academic Year:** __________________________  
**Project Guide:** ___________________________

---

## Certificate
This is to certify that the mini project entitled **“CampusCart – Online College Stationery & Prepaid Printing Management System”** is a bonafide work carried out by __________________ under the guidance of __________________ in partial fulfilment of the requirements of the Python Programming course.

Guide Signature: ____________  HOD Signature: ____________

## Declaration
I hereby declare that this project report is an account of work carried out by me/us under the guidance of __________________. The work presented is original to the best of my/our knowledge and has not been submitted elsewhere for an academic award.

Student Signature: __________________

## Acknowledgement
I express my sincere gratitude to our project guide, faculty members and the Department for their guidance and support. I also thank the college tuck-shop staff and students for helping identify the practical problems addressed by this project.

## Abstract
CampusCart is a web-based college stationery and prepaid printing management system developed using Python Flask and SQLite. The system provides students and faculty with a digital platform to browse stationery products, check stock availability, create orders and track collection status. Its Print & Collect module allows users to upload PDF, DOC, DOCX, JPG and PNG files, choose printing preferences such as colour mode, single- or double-sided printing and number of copies, view the calculated price and complete payment before the print job enters the shop queue. Staff can manage products, update inventory, process orders, download print files and update job statuses. The system also provides administrative reports and CSV-based data analysis. CampusCart aims to reduce queues, prevent unpaid/uncollected print jobs and improve the organization of tuck-shop operations.

## Chapter 1 – Introduction
College students and faculty frequently purchase stationery and require printed academic documents. A manual process can result in queues, uncertainty about product availability, order confusion and waiting time at the printing counter. CampusCart proposes a centralized web application through which users can place stationery orders and submit prepaid printing requests before visiting the tuck shop.

## Chapter 2 – Problem Statement and Objectives
### Problem Statement
The college tuck shop uses a manual ordering system, causing long queues, waiting times, order confusion and difficulty in checking item availability. Printing requests made at the counter can also create delays and may result in wastage when print jobs are not collected.

### Objectives
- Reduce waiting time and queues.
- Enable students and faculty to order stationery online.
- Display product availability.
- Allow users to upload documents and configure printing.
- Collect online payment before printing.
- Allow users to track order and print-job status.
- Improve inventory and order management.
- Generate reports for sales and printing activity.

## Chapter 3 – Existing and Proposed System
### Existing System
Orders and printing requests are handled manually at the tuck shop. Users may need to wait to check stock, place orders, submit files, specify print preferences and pay.

### Proposed System
CampusCart provides online stationery browsing, cart-based ordering, prepaid print requests and staff-side order management. Payment confirmation is required before a print job enters the paid queue. Staff prepare the job and update its status to Ready for Collection.

## Chapter 4 – Requirements
### Software Requirements
- Python 3.10 or above
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite
- HTML, CSS and JavaScript
- PyMuPDF and Pillow
- Razorpay test integration (optional configuration)
- pandas, NumPy and Matplotlib

### Hardware Requirements
- Computer/laptop for hosting and administration
- Smartphone or computer with a web browser
- Internet/local network connection
- Printer and document-printing workstation

## Chapter 5 – System Design
The application follows a three-layer architecture:
1. Presentation layer: browser interface built using HTML, CSS and JavaScript.
2. Application layer: Flask routes, business logic, authentication and payment verification.
3. Data layer: SQLite database and protected document storage.

### Main Modules
- Authentication and user management
- Stationery catalogue and cart
- Printing file upload and configuration
- Payment processing
- Admin and inventory management
- Reporting and analytics

### Database Entities
Users, Categories, Products, Stationery Orders, Order Items, Print Jobs, Payments and Inventory Logs.

## Chapter 6 – Python Concepts Used
The project uses variables, data types, operators, type conversion, conditional statements, loops, functions, lists, tuples, sets, dictionaries, string operations, datetime, file handling, CSV, JSON, exception handling, classes, objects, inheritance, encapsulation, modules and packages. pandas, NumPy and Matplotlib are used for report analysis and visualization. Concepts not naturally required by the application can be demonstrated using supplementary examples during the project explanation.

## Chapter 7 – Implementation
### Stationery Module
Users browse products by category, search by name, add products to a cart and place orders. Stock is checked before order creation and inventory is reduced when the order is placed.

### Print & Collect Module
Users upload supported documents, select print settings and copies, review the calculated amount and proceed to payment. PDF page count is detected automatically. DOC/DOCX and image page layout must be checked by staff before printing.

### Payment Module
The application includes a local demonstration payment mode and optional Razorpay test-mode integration. Demo mode does not charge real money. In Razorpay mode, payment signature verification is performed on the server before the print job is marked paid.

### Admin Module
Authorized staff can add products, update stock and prices, view stationery orders, download paid print jobs and update collection statuses.

### Analytics
Administrators can export records to CSV. The included analysis script uses pandas and NumPy to summarize recorded order values and Matplotlib to generate a chart.

## Chapter 8 – Testing
Test cases include valid and invalid login, product search, stock validation, cart calculations, supported and unsupported uploads, page range validation, multiple copies, payment success/failure, status updates, inventory changes and CSV export. Actual results should be recorded after running each test on the completed system.

## Chapter 9 – Results and Screenshots
Insert genuine screenshots from the running application:
1. Home page
2. Registration and login
3. Student dashboard
4. Stationery catalogue
5. Shopping cart
6. Order history
7. Print file upload
8. Print configuration
9. Payment confirmation
10. Printing queue
11. Inventory management
12. Admin dashboard
13. Reports and CSV output

## Chapter 10 – Conclusion and Future Enhancements
CampusCart demonstrates how Python can be used to develop a practical web-based ordering and printing management system. It combines stationery ordering, prepaid printing, inventory control and reporting in one application. Future enhancements may include QR-based collection, email notifications, real-time queue updates, automated document conversion, printer integration, configurable admin pricing and production payment webhooks.

## References
- Python Documentation: https://docs.python.org/3/
- Flask Documentation: https://flask.palletsprojects.com/
- Flask-SQLAlchemy Documentation: https://flask-sqlalchemy.palletsprojects.com/
- SQLite Documentation: https://www.sqlite.org/docs.html
- NumPy Documentation: https://numpy.org/doc/
- pandas Documentation: https://pandas.pydata.org/docs/
- Matplotlib Documentation: https://matplotlib.org/stable/
- Razorpay API Documentation: https://razorpay.com/docs/api/

---

**Before submission:** Fill in institution-specific details, verify the syllabus mapping against the official course handout, run and test the application, and insert genuine screenshots and actual test results. Do not submit illustrative or unverified results as completed work.
