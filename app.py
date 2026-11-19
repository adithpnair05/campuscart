import os
import uuid
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (Flask, render_template, redirect, url_for, flash, request,
                   abort, send_from_directory, send_file, jsonify, session)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
db_url = os.getenv("DATABASE_URL", "sqlite:///campuscart.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 15 * 1024 * 1024))
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["PAYMENT_MODE"] = os.getenv("PAYMENT_MODE", "DEMO").upper()
app.config["RAZORPAY_KEY_ID"] = os.getenv("RAZORPAY_KEY_ID", "")
app.config["RAZORPAY_KEY_SECRET"] = os.getenv("RAZORPAY_KEY_SECRET", "")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
PRINT_STATUSES = ["Paid / Queued", "Accepted", "Printing", "Ready for Collection", "Collected", "Rejected"]
ORDER_STATUSES = ["Placed", "Accepted", "Ready for Collection", "Collected", "Cancelled"]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    products = db.relationship("Product", backref="category", lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), default="")
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    price_paise = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    active = db.Column(db.Boolean, default=True)

class StationeryOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_paise = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(40), default="Placed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("stationery_order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price_paise = db.Column(db.Integer, nullable=False)

class PrintJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=True)
    page_count = db.Column(db.Integer, nullable=False)
    page_range = db.Column(db.String(100), default="all")
    copies = db.Column(db.Integer, nullable=False, default=1)
    colour_mode = db.Column(db.String(20), nullable=False)
    sides = db.Column(db.String(20), nullable=False)
    paper_size = db.Column(db.String(10), default="A4")
    total_paise = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(40), default="Paid / Queued")
    payment_ref = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)
    order_code = db.Column(db.String(20), nullable=False)
    amount_paise = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="created")
    gateway_payment_id = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    change_amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role not in ("admin", "staff"):
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

def money(paise):
    return f"₹{paise / 100:,.2f}"

def product_image(product):
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", (product.name or "").lower()).strip("-")
    img_dir = BASE_DIR / "static" / "images" / "products"
    for ext in ("png", "jpg", "jpeg", "webp", "svg"):
        if (img_dir / f"{slug}.{ext}").exists():
            return url_for("static", filename=f"images/products/{slug}.{ext}")
    return url_for("static", filename="images/products/default.svg")

@app.context_processor
def inject_globals():
    return {"money": money, "year": datetime.now().year, "product_image": product_image}

@app.template_filter("datetime")
def format_datetime(value):
    return value.strftime("%d %b %Y, %I:%M %p") if value else ""

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_page_count(path, extension):
    """Best-effort page count. DOC/DOCX/images are treated as one page unless converted."""
    ext = extension.lower()
    if ext == "pdf":
        try:
            import fitz
            with fitz.open(path) as pdf:
                return max(1, len(pdf))
        except Exception:
            raise ValueError("The PDF could not be opened. Please upload a valid PDF.")
    if ext in ("jpg", "jpeg", "png"):
        try:
            from PIL import Image
            with Image.open(path) as im:
                im.verify()
            return 1
        except Exception:
            raise ValueError("The image file is invalid.")
    return 1

def calculate_print_price(page_count, copies, colour, sides):
    # Configurable starter pricing in paise. Duplex is charged per physical sheet.
    rates = {
        ("bw", "single"): 200,
        ("bw", "double"): 300,
        ("colour", "single"): 1000,
        ("colour", "double"): 1500,
    }
    total_pages = page_count * copies
    if sides == "double":
        sheets = ((page_count + 1) // 2) * copies
        units = sheets
    else:
        units = total_pages
    return units * rates[(colour, sides)]

def make_code(prefix):
    return f"{prefix}-{secrets.token_hex(4).upper()}"

def razorpay_client():
    if not app.config["RAZORPAY_KEY_ID"] or not app.config["RAZORPAY_KEY_SECRET"]:
        raise RuntimeError("Razorpay credentials are missing. Configure them in .env.")
    import razorpay
    return razorpay.Client(auth=(app.config["RAZORPAY_KEY_ID"], app.config["RAZORPAY_KEY_SECRET"]))

@app.route("/")
def index():
    products = Product.query.filter_by(active=True).order_by(Product.name).limit(8).all()
    return render_template("index.html", products=products)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email and a password of at least 8 characters.", "danger")
        elif role not in ("student", "faculty"):
            flash("Invalid account type.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to CampusCart!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin_dashboard" if user.role in ("admin", "staff") else "dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    orders = StationeryOrder.query.filter_by(user_id=current_user.id).order_by(StationeryOrder.created_at.desc()).limit(5).all()
    jobs = PrintJob.query.filter_by(user_id=current_user.id).order_by(PrintJob.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", orders=orders, jobs=jobs)

@app.route("/stationery")
def stationery():
    category_id = request.args.get("category", type=int)
    search = request.args.get("q", "").strip()
    query = Product.query.filter_by(active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    return render_template("stationery.html", products=query.order_by(Product.name).all(),
                           categories=Category.query.order_by(Category.name).all(),
                           selected_category=category_id, search=search)

@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    cart_data = session.get("cart", {})
    if request.method == "POST":
        action = request.form.get("action")
        product_id = request.form.get("product_id", type=int)
        if not product_id:
            abort(400)
        product = db.session.get(Product, product_id)
        if not product or not product.active:
            flash("Product is unavailable.", "danger")
        elif action == "add":
            qty = max(1, min(99, request.form.get("quantity", 1, type=int)))
            current = int(cart_data.get(str(product_id), 0))
            cart_data[str(product_id)] = min(99, current + qty)
            session["cart"] = cart_data
            flash("Added to cart.", "success")
        elif action == "remove":
            cart_data.pop(str(product_id), None)
            session["cart"] = cart_data
        return redirect(url_for("cart"))
    lines, total = [], 0
    for pid, qty in cart_data.items():
        product = db.session.get(Product, int(pid))
        if product and product.active:
            qty = int(qty)
            subtotal = product.price_paise * qty
            lines.append({"product": product, "quantity": qty, "subtotal": subtotal})
            total += subtotal
    return render_template("cart.html", lines=lines, total=total)

@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))
    try:
        total = 0
        validated = []
        for pid, qty in cart_data.items():
            product = db.session.get(Product, int(pid))
            qty = int(qty)
            if not product or not product.active or qty < 1 or product.stock < qty:
                raise ValueError(f"Insufficient stock for {product.name if product else 'an item'}.")
            validated.append((product, qty))
            total += product.price_paise * qty
        order = StationeryOrder(code=make_code("CC"), user_id=current_user.id, total_paise=total, status="Placed")
        db.session.add(order)
        db.session.flush()
        for product, qty in validated:
            product.stock -= qty
            db.session.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                                     quantity=qty, unit_price_paise=product.price_paise))
            db.session.add(InventoryLog(product_id=product.id, change_amount=-qty, reason=f"Order {order.code}"))
        db.session.commit()
        session["cart"] = {}
        flash(f"Order {order.code} placed. Pay at the tuck shop when collecting.", "success")
        return redirect(url_for("my_orders"))
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
        return redirect(url_for("cart"))

@app.route("/orders")
@login_required
def my_orders():
    orders = StationeryOrder.query.filter_by(user_id=current_user.id).order_by(StationeryOrder.created_at.desc()).all()
    jobs = PrintJob.query.filter_by(user_id=current_user.id).order_by(PrintJob.created_at.desc()).all()
    return render_template("orders.html", orders=orders, jobs=jobs)

@app.route("/printing", methods=["GET", "POST"])
@login_required
def printing():
    if request.method == "POST":
        file = request.files.get("document")
        if not file or not file.filename:
            flash("Choose a document to upload.", "danger")
            return redirect(url_for("printing"))
        if not allowed_file(file.filename):
            flash("Only PDF, DOC, DOCX, JPG and PNG files are accepted.", "danger")
            return redirect(url_for("printing"))
        copies = request.form.get("copies", 1, type=int)
        if copies < 1 or copies > 50:
            flash("Copies must be between 1 and 50.", "danger")
            return redirect(url_for("printing"))
        colour = request.form.get("colour_mode", "bw")
        sides = request.form.get("sides", "single")
        if colour not in ("bw", "colour") or sides not in ("single", "double"):
            abort(400)
        ext = file.filename.rsplit(".", 1)[1].lower()
        safe_name = secure_filename(file.filename)
        if not safe_name or "." not in safe_name:
            safe_name = f"document.{ext}"
        stored = f"{uuid.uuid4().hex}.{ext}"
        path = UPLOAD_DIR / stored
        file.save(path)
        try:
            pages = get_page_count(path, ext)
            page_range = request.form.get("page_range", "all").strip() or "all"
            if page_range != "all":
                # Accept simple ranges such as 1-3,5; final validation is conservative.
                import re
                if not re.fullmatch(r"\d+(-\d+)?(,\d+(-\d+)?)*", page_range):
                    raise ValueError("Use a page range such as 1-3,5 or choose all pages.")
                nums = []
                for part in page_range.split(","):
                    bits = [int(x) for x in part.split("-")]
                    if bits[0] < 1 or (len(bits) == 2 and bits[1] < bits[0]) or any(x > pages for x in bits):
                        raise ValueError("Selected page range is outside the document.")
                    nums.extend(range(bits[0], bits[-1] + 1))
                pages = len(set(nums))
            total = calculate_print_price(pages, copies, colour, sides)
            file_bytes = path.read_bytes()
            job = PrintJob(code=make_code("PR"), user_id=current_user.id, original_filename=safe_name,
                           stored_filename=stored, file_data=file_bytes, page_count=pages, page_range=page_range,
                           copies=copies, colour_mode=colour, sides=sides, total_paise=total,
                           status="Payment Pending")
            db.session.add(job)
            db.session.commit()
            return redirect(url_for("print_payment", job_id=job.id))
        except Exception as exc:
            path.unlink(missing_ok=True)
            flash(str(exc), "danger")
            return redirect(url_for("printing"))
    return render_template("printing.html")

@app.route("/printing/<int:job_id>/payment", methods=["GET", "POST"])
@login_required
def print_payment(job_id):
    job = db.session.get(PrintJob, job_id)
    if not job or (job.user_id != current_user.id and current_user.role not in ("admin", "staff")):
        abort(404)
    if job.status != "Payment Pending":
        return redirect(url_for("my_orders"))
    if request.method == "POST":
        mode = app.config["PAYMENT_MODE"]
        payment = Payment(reference=make_code("PAY"), user_id=current_user.id, order_type="print",
                          order_code=job.code, amount_paise=job.total_paise, status="created")
        db.session.add(payment)
        db.session.commit()
        if mode == "DEMO":
            # Clearly labelled local demonstration only; this is not a real money transaction.
            payment.status = "paid"
            payment.gateway_payment_id = "DEMO-" + uuid.uuid4().hex[:12]
            job.payment_ref = payment.reference
            job.status = "Paid / Queued"
            db.session.commit()
            flash("Demo payment successful. No real money was charged.", "success")
            return redirect(url_for("my_orders"))
        try:
            client = razorpay_client()
            gateway_order = client.order.create({"amount": job.total_paise, "currency": "INR",
                                                 "receipt": payment.reference})
            session["pending_payment"] = {"payment_id": payment.id, "job_id": job.id,
                                          "gateway_order_id": gateway_order["id"]}
            return render_template("razorpay_checkout.html", job=job, payment=payment,
                                   gateway_order=gateway_order, key_id=app.config["RAZORPAY_KEY_ID"])
        except Exception as exc:
            payment.status = "failed"
            db.session.commit()
            flash(f"Could not start payment: {exc}", "danger")
            return redirect(url_for("print_payment", job_id=job.id))
    return render_template("print_payment.html", job=job)

@app.route("/payment/razorpay/verify", methods=["POST"])
@login_required
def verify_razorpay():
    data = request.get_json(silent=True) or {}
    pending = session.get("pending_payment")
    if not pending:
        return jsonify({"ok": False, "message": "No pending payment session."}), 400
    payment = db.session.get(Payment, pending["payment_id"])
    job = db.session.get(PrintJob, pending["job_id"])
    if not payment or not job or job.user_id != current_user.id:
        return jsonify({"ok": False, "message": "Payment session not found."}), 404
    try:
        client = razorpay_client()
        client.utility.verify_payment_signature({
            "razorpay_order_id": data.get("razorpay_order_id", ""),
            "razorpay_payment_id": data.get("razorpay_payment_id", ""),
            "razorpay_signature": data.get("razorpay_signature", "")
        })
        if data.get("razorpay_order_id") != pending["gateway_order_id"]:
            raise ValueError("Gateway order mismatch.")
        payment.status = "paid"
        payment.gateway_payment_id = data["razorpay_payment_id"]
        job.payment_ref = payment.reference
        job.status = "Paid / Queued"
        db.session.commit()
        session.pop("pending_payment", None)
        return jsonify({"ok": True, "redirect": url_for("my_orders")})
    except Exception:
        payment.status = "failed"
        db.session.commit()
        return jsonify({"ok": False, "message": "Payment verification failed."}), 400

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin/dashboard.html",
        products=Product.query.count(),
        low_stock=Product.query.filter(Product.stock <= Product.low_stock_threshold, Product.active.is_(True)).count(),
        stationery_orders=StationeryOrder.query.count(),
        print_jobs=PrintJob.query.count(),
        pending_prints=PrintJob.query.filter(PrintJob.status.in_(["Paid / Queued", "Accepted", "Printing"])).count(),
        recent_jobs=PrintJob.query.order_by(PrintJob.created_at.desc()).limit(8).all(),
        recent_orders=StationeryOrder.query.order_by(StationeryOrder.created_at.desc()).limit(8).all())

@app.route("/admin/products", methods=["GET", "POST"])
@admin_required
def admin_products():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category_name = request.form.get("category", "").strip()
        price = request.form.get("price", type=float)
        stock = request.form.get("stock", type=int)
        if not name or not category_name or price is None or price < 0 or stock is None or stock < 0:
            flash("Enter valid product details.", "danger")
        else:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()
            product = Product(name=name, category_id=category.id, price_paise=round(price*100),
                              stock=stock, description=request.form.get("description", "").strip())
            db.session.add(product)
            db.session.commit()
            flash("Product added.", "success")
        return redirect(url_for("admin_products"))
    return render_template("admin/products.html", products=Product.query.order_by(Product.name).all(),
                           categories=Category.query.all())

@app.route("/admin/products/<int:product_id>/update", methods=["POST"])
@admin_required
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        abort(404)
    stock = request.form.get("stock", type=int)
    price = request.form.get("price", type=float)
    if stock is None or stock < 0 or price is None or price < 0:
        flash("Invalid stock or price.", "danger")
    else:
        delta = stock - product.stock
        product.stock = stock
        product.price_paise = round(price * 100)
        if delta:
            db.session.add(InventoryLog(product_id=product.id, change_amount=delta, reason="Admin stock adjustment"))
        db.session.commit()
        flash("Product updated.", "success")
    return redirect(url_for("admin_products"))

@app.route("/admin/orders")
@admin_required
def admin_orders():
    return render_template("admin/orders.html",
        orders=StationeryOrder.query.order_by(StationeryOrder.created_at.desc()).all(),
        jobs=PrintJob.query.order_by(PrintJob.created_at.desc()).all(),
        statuses=ORDER_STATUSES, print_statuses=PRINT_STATUSES)

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    order = db.session.get(StationeryOrder, order_id)
    if not order:
        abort(404)
    status = request.form.get("status")
    if status not in ORDER_STATUSES:
        abort(400)
    order.status = status
    db.session.commit()
    flash("Order status updated.", "success")
    return redirect(url_for("admin_orders"))

@app.route("/admin/print/<int:job_id>/status", methods=["POST"])
@admin_required
def update_print_status(job_id):
    job = db.session.get(PrintJob, job_id)
    if not job:
        abort(404)
    status = request.form.get("status")
    if status not in PRINT_STATUSES or (status != "Rejected" and job.status == "Payment Pending"):
        abort(400)
    job.status = status
    db.session.commit()
    flash("Printing status updated.", "success")
    return redirect(url_for("admin_orders"))

@app.route("/admin/print/<int:job_id>/file")
@admin_required
def admin_print_file(job_id):
    job = db.session.get(PrintJob, job_id)
    if not job:
        abort(404)
    if job.file_data:
        from io import BytesIO
        return send_file(BytesIO(job.file_data), as_attachment=True, download_name=job.original_filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], job.stored_filename,
                               as_attachment=True, download_name=job.original_filename)

@app.route("/admin/reports")
@admin_required
def admin_reports():
    orders = StationeryOrder.query.all()
    jobs = PrintJob.query.filter(PrintJob.status != "Payment Pending").all()
    stationery_revenue = sum(o.total_paise for o in orders if o.status != "Cancelled")
    print_revenue = sum(j.total_paise for j in jobs if j.status != "Rejected")
    product_counts = {}
    for order in orders:
        for item in order.items:
            product_counts[item.product_name] = product_counts.get(item.product_name, 0) + item.quantity
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    return render_template("admin/reports.html", stationery_revenue=stationery_revenue,
                           print_revenue=print_revenue, top_products=top_products,
                           print_jobs=len(jobs), orders=len(orders))

@app.route("/admin/reports/export")
@admin_required
def export_report():
    import csv
    from io import StringIO
    from flask import Response
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Type", "Reference", "User", "Amount INR", "Status", "Created At"])
    for order in StationeryOrder.query.order_by(StationeryOrder.created_at.desc()).all():
        writer.writerow(["Stationery", order.code, order.user.name, f"{order.total_paise/100:.2f}", order.status, order.created_at.isoformat()])
    for job in PrintJob.query.order_by(PrintJob.created_at.desc()).all():
        writer.writerow(["Printing", job.code, job.user.name, f"{job.total_paise/100:.2f}", job.status, job.created_at.isoformat()])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=campuscart_report.csv"})

@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "CampusCart"})

@app.errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum upload size is 15 MB.", "danger")
    return redirect(url_for("printing"))

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page or record could not be found."), 404

def seed_database():
    db.create_all()
    if not Category.query.first():
        names = ["Writing", "Books", "Paper", "Files & Folders", "Geometry & Drawing", "Accessories"]
        categories = {name: Category(name=name) for name in names}
        db.session.add_all(categories.values())
        db.session.flush()
        samples = [
            ("Blue Ball Pen", "Smooth blue ball pen", "Writing", 10, 100),
            ("Black Ball Pen", "Black ink ball pen", "Writing", 10, 100),
            ("HB Pencil", "Standard HB pencil", "Writing", 5, 150),
            ("Highlighter Set", "Set of 4 assorted highlighters", "Writing", 80, 25),
            ("A4 Notebook", "Single-line 172 page notebook", "Books", 55, 60),
            ("Record Book", "College practical record book", "Books", 95, 40),
            ("A4 Sheets (100)", "100 sheets of A4 paper", "Paper", 60, 50),
            ("Graph Sheets (10)", "Pack of 10 graph sheets", "Paper", 20, 40),
            ("Document Folder", "A4 transparent folder", "Files & Folders", 15, 80),
            ("Spring File", "A4 spring file", "Files & Folders", 35, 45),
            ("Geometry Box", "Basic geometry instrument set", "Geometry & Drawing", 85, 20),
            ("Scale 30 cm", "Transparent ruler", "Geometry & Drawing", 15, 70),
            ("Stapler", "Compact desk stapler", "Accessories", 75, 15),
            ("Glue Stick", "20 g glue stick", "Accessories", 30, 35),
        ]
        for name, desc, cat, price, stock in samples:
            db.session.add(Product(name=name, description=desc, category_id=categories[cat].id,
                                   price_paise=price*100, stock=stock))
    admin_email = os.getenv("CAMPUSCART_ADMIN_EMAIL", "admin@campuscart.local").strip().lower()
    if not User.query.filter_by(email=admin_email).first():
        admin = User(name="CampusCart Admin", email=admin_email, role="admin")
        admin.set_password(os.getenv("CAMPUSCART_ADMIN_PASSWORD", "Admin@12345"))
        db.session.add(admin)
    db.session.commit()

with app.app_context():
    seed_database()

if __name__ == "__main__":
    app.run(debug=True)
