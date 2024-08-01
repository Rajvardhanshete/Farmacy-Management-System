from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from fpdf import FPDF
import smtplib

# import mysql.connector

LOGIN = False
DAY = datetime.now()
today = (f"{DAY.day}-{DAY.month}-{DAY.year}")
BATCH= (DAY.strftime("%d"))+(DAY.strftime("%b"))+(DAY.strftime("%y"))
bill_no = (DAY.strftime("%y"))+(DAY.strftime("%m"))
creat = 1
dictmedi = {}
newcust = False
get_custnum = None
get_custname = None
price_medi = None
msg_medi_not_found= False
medicine_bill_data = []
pdf_gen= False
total = 0

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/pharmacywbs"
app.secret_key = "LOGIN"

db = SQLAlchemy(app)



class Customer(db.Model):
    """
    cust_id, cust_name, cust_contact, cust_address, doctor_name ,gender
    """
    cust_id : Mapped[int] = mapped_column(primary_key=True)
    cust_name : Mapped[str] = mapped_column(nullable=False)
    cust_contact: Mapped[str] = mapped_column(nullable=False)
    cust_address : Mapped[str] = mapped_column(nullable=False)
    doctor_name : Mapped[str] = mapped_column(nullable=False)
    gender : Mapped[str] = mapped_column(nullable=False)


class Supplier(db.Model):
    """ field name:
     sup_id, sup_name, sup_email, sup_contact, sup_address, sup_company
     """
    sup_id : Mapped[int] = mapped_column(primary_key=True)
    sup_name : Mapped[str] = mapped_column(nullable=False)
    sup_email: Mapped[str] = mapped_column(nullable=False)
    sup_contact : Mapped[str] = mapped_column(nullable=False)
    sup_address : Mapped[str] = mapped_column(nullable=False)
    sup_company : Mapped[str] = mapped_column(nullable=False)


class Admin(db.Model):
    """ Admin login parameters"""
    admin_id : Mapped[int] = mapped_column(primary_key=True, nullable=False)
    admin_name: Mapped[str] = mapped_column(nullable=False)
    admin_uname: Mapped[str] = mapped_column(nullable=False)
    admin_pass: Mapped[str] = mapped_column(nullable=False)
    admin_address : Mapped[str] = mapped_column(nullable=False)


class Stock(db.Model):
    """Stock of Medicines"""
    st_id : Mapped[int] = mapped_column(primary_key=True, nullable=False)
    medi_name : Mapped[str] = mapped_column(nullable=False)
    company_name : Mapped[str] = mapped_column(nullable=False)
    quantity : Mapped[str] = mapped_column(nullable=False)
    min_quantity : Mapped[int] = mapped_column(nullable=False)
    exp_date : Mapped[datetime] = mapped_column(nullable=False)
    batch_id : Mapped[str] = mapped_column(nullable=False)
    ratepermedi : Mapped[int] = mapped_column(nullable=False)
    sup_id : Mapped[int] = mapped_column(nullable=False)


class Inovice(db.Model):
    """Stock of Medicines"""
    invoice_no : Mapped[int] = mapped_column(primary_key=True, nullable=False)
    cust_id : Mapped[str] = mapped_column(nullable=False)
    date : Mapped[str] = mapped_column(nullable=False)
    total : Mapped[int] = mapped_column(nullable=False)
    pdf : Mapped[str] = mapped_column(nullable=False)



with app.app_context():
    db.create_all()


@app.route("/logout")
def logout():
    print("Logout")
    session['loggedin'] = False
    session.pop('adminname', None)
    session.pop('password', None)

    return render_template("login.html")


@app.route("/", methods=["GET", "POST"])
def login():
    print("Login")
    session['loggedin'] = False
    if request.method == 'POST':
        admin_name = db.session.execute(db.select(Admin.admin_uname))
        admin_pass = db.session.execute(db.select(Admin.admin_pass))
        user = request.form.get("userid")
        passwd = request.form.get("password")
        if (str((admin_name.first()[0])) == str(user)) and (str(admin_pass.first()[0]) == str(passwd)):
            # flash('You were successfully logged in')
            session['adminname'] = user
            session['password'] = passwd
            session['loggedin'] = True

            adminname = session['adminname']
            passw = session['password']
            return redirect(url_for("index", LOGIN=user))
        else:
            message = "Wrong UserName or Password"
            return render_template("login.html", message=message)
    return render_template("login.html")


@app.route("/index")
def index():
    print("Dashbord")
    if session["loggedin"] == True:
        print("test1")
        custdata = Customer.query.all()
        supdata = Supplier.query.all()
        totalmedicine = Stock.query.all()
        inovice = Inovice.query.all()
        exp_data = Stock.query.filter( Stock.exp_date < DAY.year).all()
        out_data = Stock.query.filter( Stock.quantity <= 0).all()
        totalexp = len(exp_data)
        totalout = len(out_data)
        customer=(len(custdata))
        supplier=(len(supdata))
        totalinovice = len(inovice)
        totalmedicines =(len(totalmedicine))
    else:
        return redirect(url_for("login"))
    print("test2")
    return render_template("index.html", customer=(customer), supplier=supplier, totalmedicines=totalmedicines, totalexp=totalexp, totalout=totalout, totalinovice=totalinovice)


@app.route("/profile")
def profile():
    if session["loggedin"] == True:
        print("loggedin")
        admin_data = Admin.query.all()
        return render_template("profile.html", admin_data=admin_data)
    else:
        print("pro 3")
        return redirect(url_for("login"))


@app.route("/inovice")
def inovice():
    if session["loggedin"] == True:
        print("inovice")
        return redirect(url_for("innovice"))
    else:
        return redirect(url_for("login"))


@app.route("/sales_report")
def sales_report():
    if session["loggedin"] == True:
        print("Sales Report")
        return redirect(url_for("sales_report"))
    else:
        return redirect(url_for("login"))


@app.route("/innovice", methods=['GET', 'POST'])
def innovice():
    global newcust, get_custname, get_custnum, price_medi,pdf_gen, msg_medi_not_found, total
    print("innovice")

    if request.method == 'POST':
        newcust = False
        if request.form.get("add") == "add":
            price_medi = None
            msg_medi_not_found = False
            print("post of innovice")
            name_cust = request.form.get("cust_name")
            num_cust = request.form.get("cust_name")
            name_medi = request.form.get("medicines")
            quant_meid = request.form.get("quantity")
            try:
                meid_price = Stock.query.filter(Stock.medi_name == name_medi).first()
                price_medi = int(quant_meid) * int(meid_price.ratepermedi)
                print(price_medi)

            except:
                print("failed to fetch price")
            if name_medi != "" and quant_meid != "" and price_medi != None:
                dictmedi.update({name_medi : [quant_meid, price_medi]})
                title = request.form.get("medicines")
                quantity = request.form.get("quantity")
                if title and quantity and price_medi:
                    medicine_bill_data.append({
                        'Medicines' : title,
                        'Quantity' : quantity,
                        'Price' : price_medi
                    })
                    total += price_medi
                    print("total ",total)

            else:
                msg_medi_not_found = True
        btnval = request.form.get("delete")
        try:
            if btnval != None:
                print("button delete")
                dictmedi.pop(btnval)
                total -= price_medi
                print(total)
        except Exception as e:
            print(e)
        try:
            for k, v in dictmedi.items():
                print(k,v[0],v[1])
                if k == None:
                    dictmedi.pop(k)
        except Exception as e:
            print(e)
        if request.form.get("search") == "search":
            get_custname = request.form.get("cust_name")
            print(get_custname)
            get_custnum = request.form.get("cust_num")
            check = Customer.query.filter(Customer.cust_name == get_custname, Customer.cust_contact == get_custnum).first()
            print(check)
            if check == None:
                print("not found")
                newcust = True
            else:
                newcust = False

        #gerate pdf and update table
        if request.form.get("generate") == "generate":
            print("generate pdf test1")
            get_custname = request.form.get("cust_name")
            get_custnum = request.form.get("cust_num")
            check = Customer.query.filter(Customer.cust_name == get_custname,
                                          Customer.cust_contact == get_custnum).first()
            pdf_file = generate_pdf_file()
            pdf_gen = True
            get_custname = request.form.get("cust_name")
            medicine_bill_data.clear()
            print("medicine cleared")
            return send_file(pdf_file, as_attachment=True, download_name=f"{get_custname}.pdf")

        if request.form.get("gen_pdf") == "gen_pdf":
            print("pdf_insertion start")
            get_custname = request.form.get("cust_name")
            get_custnum = request.form.get("cust_num")
            check = Customer.query.filter(Customer.cust_name == get_custname,
                                          Customer.cust_contact == get_custnum).first()
            try:
                path =f"./{get_custname}.pdf"
                with open(path,"rb") as file:
                    upfile = file.read()
                check = Customer.query.filter(Customer.cust_name == get_custname,
                                              Customer.cust_contact == get_custnum).first()
                for book in medicine_bill_data:
                    total += int(book['Price'])
                inovice_insert = Inovice(cust_id=check.cust_id, date=today, total=total, pdf=upfile)
                print("insert total:",total)
                try:
                    db.session.add(inovice_insert)
                    db.session.commit()
                    print("pdf inserted")
                except Exception as e:
                    print(e)
            except Exception as e:
                print(e)
    return render_template("innovice.html", dictmedi=dictmedi, invoice_number=bill_no, date=DAY.date(),total=total, newcust=newcust, get_custname=(get_custname), get_custnum=get_custnum, msg_medi_not_found=msg_medi_not_found)


def generate_pdf_file():
    global total
    get_name = request.form.get("cust_name")
    mediinvpdf = FPDF()
    mediinvpdf.add_page()
    mediinvpdf.set_font("Arial", size=10)

    # effective page width
    epw = mediinvpdf.w - 2 * mediinvpdf.l_margin

    # column width
    col_width = epw / 4.5

    # font size
    fs = mediinvpdf.font_size

    # heading of file
    mediinvpdf.cell(200, 10, txt="Customer Information", ln=2, align="C")
    mediinvpdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")
    mediinvpdf.cell(200, 10, txt=f"Customer Name : {get_name}", ln=2, align="L")
    mediinvpdf.cell(200, 10, txt=f"Bill No : {bill_no}", ln=2, align="L")

    # table data
    mediinvpdf.cell(5, 2 * fs, txt="ID", align="C", border=1)
    mediinvpdf.cell(col_width + 10, 2 * fs, txt="Medicine Name", align="C", border=1)
    mediinvpdf.cell(col_width - 10, 2 * fs, txt="Quantity", align="C", border=1)
    mediinvpdf.cell(col_width, 2 * fs, txt="Price", align="C", border=1)
    mediinvpdf.ln(fs * 2)
    i = 1
    for row in medicine_bill_data:
        # Enter datasup_name in colums
        mediinvpdf.cell(5, 2 * fs, str(i), align="C", border=1)
        mediinvpdf.cell(col_width + 10, 2 * fs, str(row['Medicines']), align="C", border=1)
        mediinvpdf.cell(col_width - 10, 2 * fs, str(row['Quantity']), align="C", border=1)
        mediinvpdf.cell(col_width, 2 * fs, str(row['Price']), align="C", border=1)
        mediinvpdf.ln(fs * 2)
        i+=1

    mediinvpdf.cell((col_width * 3)+5, 2 * fs, str(f"total : {total}"), align="R", border=1)

    mediinvpdf.output(f"{get_name}.pdf")

    total = 0
    for book in medicine_bill_data:
        total += int(book['Price'])

        try:
            update_medi = Stock.query.filter(Stock.medi_name == book['Medicines']).first()
            if Stock.query.filter(Stock.medi_name == book['Medicines']).first():
                print("Medicine is found")
                update_medi.quantity = (int(update_medi.quantity) - int(book["Quantity"]))
                print(update_medi.quantity)
                update_medi.verified = True
                db.session.commit()
                print("if.. Medicine is updated..")
        except Exception as e:
            print(e)

        check = Stock.query.filter(Stock.quantity < Stock.min_quantity).all()
        print(check)
        for i in check:

            email = Supplier.query.filter(Supplier.sup_id == i.sup_id).first()
            send = (email.sup_email)

            myemail = "rajvardhans2223@gmail.com"
            mypass = "yjkfnngbiasebluf"

            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=myemail, password=mypass)
                connection.sendmail(from_addr=myemail,
                                    to_addrs=send,
                                    msg=f"Subject: To order the Medicine, \n\n We need {i.medi_name} medicine of {i.company_name} company \n because this will running out of stock.\n"
                                    )
    return mediinvpdf, total


@app.route("/customer_report", methods=['GET', 'POST'])
def customer_report():
    if session["loggedin"] == True:
        print("test login")
        customer_data = Customer.query.all()

        if request.method == 'POST':
            print("test  post")
            if request.form.get("printcust") == "printcust":
                print("test cust report")
                custpdf = FPDF()
                custpdf.add_page()
                custpdf.set_font("Arial", size=10)

                #effective page width
                epw = custpdf.w - 2 * custpdf.l_margin

                #column width
                col_width = epw / 4.5

                #font size
                fs = custpdf.font_size

                #heading of file
                custpdf.cell(200, 10, txt="Customer Information", ln=2, align="C")
                custpdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")

                #table data
                custpdf.cell(5, 2 * fs, txt="ID", align="C", border=1)
                custpdf.cell(col_width + 10, 2 * fs, txt="Name", align="C", border=1)
                custpdf.cell(col_width - 10, 2 * fs, txt="Contact", align="C", border=1)
                custpdf.cell(col_width, 2 * fs, txt="Address", align="C", border=1)
                custpdf.cell(col_width - 5, 2 * fs, txt="Doctor", align="C", border=1)
                custpdf.cell(col_width - 20, 2 * fs, txt="Gender", align="C", border=1)
                custpdf.ln(fs*2)

                for row in customer_data:
                    # Enter datasup_name in colums
                    custpdf.cell(5, 2 * fs, str(row.cust_id ), align="C", border=1)
                    custpdf.cell(col_width + 10, 2 * fs, str(row.cust_name), align="C", border=1)
                    custpdf.cell(col_width - 10, 2 * fs, str(row.cust_contact), align="C", border=1)
                    custpdf.cell(col_width, 2 * fs, str(row.cust_address), align="C", border=1)
                    custpdf.cell(col_width - 5, 2 * fs, str(row.doctor_name), align="C", border=1)
                    custpdf.cell(col_width - 20, 2 * fs, str(row.gender), align="C", border=1)
                    custpdf.ln(fs * 2)

                custpdf.output("Customer_list.pdf")

    else:
        return redirect(url_for("login"))
    return render_template("customer_report.html", customer_data=customer_data)


@app.route("/out_of_stock", methods=['GET', 'POST'])
def out_of_stock():
    if session["loggedin"] == True:
        print("test login")
        medicine_data =Stock.query.filter( Stock.quantity <= 0).all()
        if request.method == 'POST':
            print("test post")
            if request.form.get("printoutmedi") == "printoutmedi":
                print("test medi out of stock report")
                outstmedipdf = FPDF()
                outstmedipdf.add_page()
                outstmedipdf.set_font("Arial", size=10)

                # effective page width
                epw = outstmedipdf.w - 2 * outstmedipdf.l_margin

                # column width
                col_width = epw / 4.5

                # font size
                fs = outstmedipdf.font_size

                # heading of file
                outstmedipdf.cell(200, 10, txt="Out Of Stock Medicine Information", ln=2, align="C")
                outstmedipdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")

                # table data
                outstmedipdf.cell(5, 2 * fs, txt="ID", align="C", border=1)
                outstmedipdf.cell(col_width - 15, 2 * fs, txt="Medicine Name", align="C", border=1)
                outstmedipdf.cell(col_width - 25, 2 * fs, txt="Company", align="C", border=1)
                outstmedipdf.cell(col_width - 25, 2 * fs, txt="Quantity", align="C", border=1)
                outstmedipdf.cell(col_width - 25, 2 * fs, txt="Min. QNT", align="C", border=1)
                outstmedipdf.cell(col_width - 25, 2 * fs, txt="Exp. Date", align="C", border=1)
                outstmedipdf.cell(col_width - 25, 2 * fs, txt="Batch", align="C", border=1)
                outstmedipdf.cell(col_width - 25, 2 * fs, txt="Rate", align="C", border=1)
                outstmedipdf.cell(col_width - 20, 2 * fs, txt="Supplier ID", align="C", border=1)
                outstmedipdf.cell(col_width - 10, 2 * fs, txt="Supplier Name", align="C", border=1)
                outstmedipdf.ln(fs * 2)

                for row in medicine_data:
                    sup_name = Supplier.query.filter(Supplier.sup_id == row.sup_id).first()
                    # Enter datasup_name in colums
                    outstmedipdf.cell(5, 2 * fs, str(row.st_id), align="C", border=1)
                    outstmedipdf.cell(col_width - 15, 2 * fs, str(row.medi_name), align="C", border=1)
                    outstmedipdf.cell(col_width - 25, 2 * fs, str(row.company_name), align="C", border=1)
                    outstmedipdf.cell(col_width - 25, 2 * fs, str(row.quantity), align="C", border=1)
                    outstmedipdf.cell(col_width - 25, 2 * fs, str(row.min_quantity), align="C", border=1)
                    outstmedipdf.cell(col_width - 25, 2 * fs, str(row.exp_date), align="C", border=1)
                    outstmedipdf.cell(col_width - 25, 2 * fs, str(row.batch_id), align="C", border=1)
                    outstmedipdf.cell(col_width - 25, 2 * fs, str(row.ratepermedi), align="C", border=1)
                    outstmedipdf.cell(col_width - 20, 2 * fs, str(row.sup_id), align="C", border=1)
                    outstmedipdf.cell(col_width - 10, 2 * fs, str(sup_name.sup_name), align="C", border=1)
                    outstmedipdf.ln(fs * 2)

                outstmedipdf.output("Out_Stock_Medicine_list.pdf")
    else:
        return redirect(url_for("login"))
    return render_template("out_of_stock.html",medicine_data=medicine_data)


@app.route("/expired_medi", methods=['GET', 'POST'])
def expired_medi():
    if session["loggedin"] == True:
        print("test login")
        medicine_data = Stock.query.filter( Stock.exp_date < DAY.year).all()
        if request.method == 'POST':
            print("test post")
            if request.form.get("printexpmedi") == "printexpmedi":
                print("test medi report")
                expmedipdf = FPDF()
                expmedipdf.add_page()
                expmedipdf.set_font("Arial", size=10)

                # effective page width
                epw = expmedipdf.w - 2 * expmedipdf.l_margin

                # column width
                col_width = epw / 4.5

                # font size
                fs = expmedipdf.font_size

                # heading of file
                expmedipdf.cell(200, 10, txt="Expired Medicine Information", ln=2, align="C")
                expmedipdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")

                # table data
                expmedipdf.cell(5, 2 * fs, txt="ID", align="C", border=1)
                expmedipdf.cell(col_width - 15, 2 * fs, txt="Medicine Name", align="C", border=1)
                expmedipdf.cell(col_width - 25, 2 * fs, txt="Company", align="C", border=1)
                expmedipdf.cell(col_width - 25, 2 * fs, txt="Quantity", align="C", border=1)
                expmedipdf.cell(col_width - 25, 2 * fs, txt="Min. QNT", align="C", border=1)
                expmedipdf.cell(col_width - 25, 2 * fs, txt="Exp. Date", align="C", border=1)
                expmedipdf.cell(col_width - 25, 2 * fs, txt="Batch", align="C", border=1)
                expmedipdf.cell(col_width - 25, 2 * fs, txt="Rate", align="C", border=1)
                expmedipdf.cell(col_width - 20, 2 * fs, txt="Supplier ID", align="C", border=1)
                expmedipdf.cell(col_width - 10, 2 * fs, txt="Supplier Name", align="C", border=1)
                expmedipdf.ln(fs * 2)

                for row in medicine_data:
                    sup_name = Supplier.query.filter(Supplier.sup_id == row.sup_id).first()
                    # Enter datasup_name in colums
                    expmedipdf.cell(5, 2 * fs, str(row.st_id), align="C", border=1)
                    expmedipdf.cell(col_width - 15, 2 * fs, str(row.medi_name), align="C", border=1)
                    expmedipdf.cell(col_width - 25, 2 * fs, str(row.company_name), align="C", border=1)
                    expmedipdf.cell(col_width - 25, 2 * fs, str(row.quantity), align="C", border=1)
                    expmedipdf.cell(col_width - 25, 2 * fs, str(row.min_quantity), align="C", border=1)
                    expmedipdf.cell(col_width - 25, 2 * fs, str(row.exp_date), align="C", border=1)
                    expmedipdf.cell(col_width - 25, 2 * fs, str(row.batch_id), align="C", border=1)
                    expmedipdf.cell(col_width - 25, 2 * fs, str(row.ratepermedi), align="C", border=1)
                    expmedipdf.cell(col_width - 20, 2 * fs, str(row.sup_id), align="C", border=1)
                    expmedipdf.cell(col_width - 10, 2 * fs, str(sup_name.sup_name), align="C", border=1)
                    expmedipdf.ln(fs * 2)

                expmedipdf.output("Expired_Medicine_list.pdf")
    else:
        return redirect(url_for("login"))
    return render_template("expired_medi.html",medicine_data=medicine_data)


@app.route("/report")
def report():
    if session["loggedin"] == True:
        print("test login")
    else:
        print("failed")
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/total_medicine", methods=['GET','POST'])
def total_medicine():
    if session["loggedin"] == True:
        print("test login")
        # get medicine data from database
        medicine_data = Stock.query.all()
        if request.method == 'POST':
            print("test  post")
            if request.form.get("printmed") == "printmed":
                print("test meidcine report")
                medipdf = FPDF()
                medipdf.add_page()
                medipdf.set_font("Arial", size=10)

                #effective page width
                epw = medipdf.w - 2 * medipdf.l_margin

                #column width
                col_width = epw / 4.5

                #font size
                fs = medipdf.font_size

                #heading of file
                medipdf.cell(200, 10, txt="Medicine Information", ln=2, align="C")
                medipdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")

                #table data
                medipdf.cell(5, 2 * fs, txt="ID", align="C", border=1)
                medipdf.cell(col_width - 15, 2 * fs, txt="Medicine Name", align="C", border=1)
                medipdf.cell(col_width - 25, 2 * fs, txt="Company", align="C", border=1)
                medipdf.cell(col_width - 25, 2 * fs, txt="Quantity", align="C", border=1)
                medipdf.cell(col_width - 25, 2 * fs, txt="Min. QNT", align="C", border=1)
                medipdf.cell(col_width - 25, 2 * fs, txt="Exp. Date", align="C", border=1)
                medipdf.cell(col_width - 25, 2 * fs, txt="Batch", align="C", border=1)
                medipdf.cell(col_width - 25, 2 * fs, txt="Rate", align="C", border=1)
                medipdf.cell(col_width - 20, 2 * fs, txt="Supplier ID", align="C", border=1)
                medipdf.cell(col_width - 10, 2 * fs, txt="Supplier Name", align="C", border=1)
                medipdf.ln(fs*2)

                for row in medicine_data:
                    sup_name = Supplier.query.filter(Supplier.sup_id == row.sup_id).first()
                    # Enter datasup_name in colums
                    medipdf.cell(5, 2 * fs, str(row.st_id), align="C", border=1)
                    medipdf.cell(col_width - 15, 2 * fs, str(row.medi_name), align="C", border=1)
                    medipdf.cell(col_width - 25, 2 * fs, str(row.company_name), align="C", border=1)
                    medipdf.cell(col_width - 25, 2 * fs, str(row.quantity), align="C", border=1)
                    medipdf.cell(col_width - 25, 2 * fs, str(row.min_quantity), align="C", border=1)
                    medipdf.cell(col_width - 25, 2 * fs, str(row.exp_date), align="C", border=1)
                    medipdf.cell(col_width - 25, 2 * fs, str(row.batch_id), align="C", border=1)
                    medipdf.cell(col_width - 25, 2 * fs, str(row.ratepermedi), align="C", border=1)
                    medipdf.cell(col_width - 20, 2 * fs, str(row.sup_id), align="C", border=1)
                    medipdf.cell(col_width - 10, 2 * fs, str(sup_name.sup_name), align="C", border=1)
                    medipdf.ln(fs * 2)

                medipdf.output("Medicine_list.pdf")

    else:
        return redirect(url_for("login"))
    return render_template("medicine_report.html", medicine_data=medicine_data)


@app.route("/total_supplier", methods=['GET', 'POST'])
def total_supplier():
    if session["loggedin"] == True:
        print("test login")
        # get supplier data from database
        supplier_data = Supplier.query.all()

        if request.method == 'POST':
            print("test post post")
            if request.form.get("printsup") == "printsup":
                print("test Signup report generate")
                suppdf = FPDF()
                suppdf.add_page()
                suppdf.set_font("Arial", size=10)

                #effective page width
                epw = suppdf.w - 2 * suppdf.l_margin

                #column width
                col_width = epw / 4.5

                #font size
                fs = suppdf.font_size

                #heading of file
                suppdf.cell(200, 10, txt="Supplier Information", ln=2, align="C")
                suppdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")

                #table data
                suppdf.cell(5, 2 * fs, txt="ID", align="C", border=1)
                suppdf.cell(col_width, 2 * fs, txt="Name", align="C", border=1)
                suppdf.cell(col_width+20, 2 * fs, txt="Email", align="C", border=1)
                suppdf.cell(col_width-20, 2 * fs, txt="Contact", align="C", border=1)
                suppdf.cell(col_width-15, 2 * fs, txt="Address", align="C", border=1)
                suppdf.cell(col_width-15, 2 * fs, txt="Company", align="C", border=1)
                suppdf.ln(fs*2)

                for row in supplier_data:
                    # Enter datasup_name in colums
                     suppdf.cell(5, 2 * fs, str(row.sup_id), align="C", border=1)
                     suppdf.cell(col_width, 2 * fs, str(row.sup_name), align="C", border=1)
                     suppdf.cell(col_width+20, 2 * fs, str(row.sup_email), align="C", border=1)
                     suppdf.cell(col_width-20, 2 * fs, str(row.sup_contact), align="C", border=1)
                     suppdf.cell(col_width-15, 2 * fs, str(row.sup_address), align="C", border=1)
                     suppdf.cell(col_width-15, 2 * fs, str(row.sup_company), align="C", border=1)
                     suppdf.ln(fs * 2)

                suppdf.output("Supplier_list.pdf")


    else:
        print("failed to total supplier")
        return redirect(url_for("login"))
    return render_template("supplier_report.html", supplier_data=supplier_data)


@app.route("/total_inovice", methods=['GET','POST'])
def total_inovice():
    if session["loggedin"] == True:
        print("loggedin")
        # get inovice data from database
        inovice_data = Inovice.query.all()
        if request.method == 'POST':
                if request.form.get("printinv") == "printinv":
                    print("inv print")
                    invpdf = FPDF()
                    invpdf.add_page()
                    invpdf.set_font("Arial", size=10)

                    # effective page width
                    epw = invpdf.w - 2 * invpdf.l_margin

                    # column width
                    col_width = epw / 4.5

                    # font size
                    fs = invpdf.font_size

                    # heading of file
                    invpdf.cell(200, 10, txt="Inovice Information", ln=2, align="C")
                    invpdf.cell(200, 10, txt=f"Date: {DAY.day}/{DAY.month}/{DAY.year}", ln=2, align="L")

                    # table data
                    invpdf.cell(30, 2 * fs, txt="")
                    invpdf.cell(10, 2 * fs, txt="IN. ID", align="C", border=1)
                    invpdf.cell(col_width-20, 2 * fs, txt="Cust ID", align="C", border=1)
                    invpdf.cell(col_width, 2 * fs, txt="Cust Name", align="C", border=1)
                    invpdf.cell(col_width + 20, 2 * fs, txt="Date", align="C", border=1)
                    invpdf.ln(fs * 2)

                    for row in inovice_data:
                        cust_name = Customer.query.filter(Customer.cust_id==row.cust_id).first()
                        # Enter datasup_name in colums
                        invpdf.cell(30, 2 * fs, txt="")
                        invpdf.cell(10, 2 * fs, str(row.invoice_no ), align="C", border=1)
                        invpdf.cell(col_width-20, 2 * fs, str(row.cust_id), align="C", border=1)
                        invpdf.cell(col_width, 2 * fs, str(cust_name.cust_name), align="C", border=1)
                        invpdf.cell(col_width + 20, 2 * fs, str(row.date), align="C", border=1)
                        invpdf.ln(fs * 2)

                    invpdf.output("Inovice_list.pdf")
                for i in inovice_data:
                    try:
                        if request.form.get("download") in str(i.pdf):
                            cust_name = Customer.query.filter(Customer.cust_id==i.cust_id).first()
                            write_file(i.pdf, str(cust_name.cust_name) + '.pdf')
                            print("file write")
                    except Exception as e:
                        print(e)

    else:
        return redirect(url_for("login"))
    return render_template("inovice_report.html", inovice_data=inovice_data)


def write_file(data, filename):
    with open(f"C:/Users/rajva/Downloads/Bill_of_{filename}", 'wb') as f:
        print("file write complete")
        f.write(data)

    return send_file(filename, as_attachment=True, download_name=f"{get_custname}.pdf")


@app.route("/addsupplier", methods=["GET", "POST"])
def addsupplier():
    print(LOGIN)
    if request.method == 'POST':
        """Add supllier data"""
        print("Request post")
        """names of tag: sup_id, sup_name, sup_email, sup_number, sup_address,sup_cmpname"""
        name = request.form.get("sup_name")
        print(name)
        email = request.form.get("sup_email")
        print(email)
        number = request.form.get("sup_number")
        print(number)
        company = request.form.get("sup_cmpname")
        print(company)
        address = request.form.get("sup_address")
        print(address)
        sup = Supplier(sup_name=name, sup_email=email, sup_contact=number, sup_address=address, sup_company=company)
        try:
            db.session.add(sup)
            db.session.commit()
            print("inserted....")
        except Exception as e:
            print(e)
            return render_template("error.html", error_message="Failed to insert")
    return render_template("addsupplier.html")


@app.route("/addcustomer", methods=["POST", "GET"])
def addcustomer():
    print("test1")
    if request.method == 'POST':
        """Add Customer data"""
        """ cust_id, cust_name, cust_contact, cust_address, doctor_name, gender"""
        name = request.form.get("cust_name")
        print(name)
        address = request.form.get("cust_address")
        print(address)
        number = request.form.get("cust_number")
        print(number)
        doctor = request.form.get("doctor_name")
        print(doctor)
        company = request.form.get("sup_cmpname")
        print(company)
        gender = request.form.get("form_group")
        print(gender)
        cust = Customer(cust_name=name, cust_contact=number, cust_address=address, doctor_name=doctor, gender=gender)
        try:
            db.session.add(cust)
            db.session.commit()
            print("inserted....")
        except Exception as e:
            print(e)
            return render_template("error.html",error_message="Failed to insert")
    return render_template("addcustomer.html")


@app.route("/addmedicine", methods=["GET", "POST"])
def addmedicine():
    if request.method == "POST":
        """Add Medecine dataa"""
        """medicine_name , manufacturer_name, quantity, rate, mrp, expiry-date, batch, supplier_contact"""
        medi_name = request.form.get("medicine_name")
        print(medi_name)
        company = request.form.get("manufacturer_name")
        print(company)
        quany = request.form.get("quantity")
        print(quany)
        min_quantity = request.form.get("min_quantity")
        print(min_quantity)
        expdate = request.form.get("expiry-date")
        print(expdate)
        batch = BATCH
        print(batch)
        ratepermedic = request.form.get("rate")
        sup_num = request.form.get("supplier_contact")
        sup_contact_data= db.one_or_404(
            db.select(Supplier).filter_by(sup_contact=sup_num)
        )
        id_sup = (sup_contact_data.sup_id)
        print(id_sup)
        medi = Stock(medi_name=medi_name,company_name=company,quantity=quany, min_quantity=min_quantity, exp_date=expdate, batch_id=batch, ratepermedi=ratepermedic, sup_id=id_sup)
        try:
            medi_check = Stock.query.filter(Stock.medi_name == medi_name).first()
            if Stock.query.filter(Stock.medi_name == medi_name, Stock.batch_id == batch).first():
                print("same")
                medi_check.quantity = (int(medi_check.quantity) + int(quany))
                print(medi_check.quantity)
                medi_check.verified = True
                db.session.commit()
                print("if block and updated..")
            else:
                print(medi_check)
                db.session.add(medi)
                db.session.commit()
                print("else")
            print("inserted....")
        except Exception as e:
            print("error : ",e)
            return render_template("error.html",error_message="Failed to insert")

    return render_template("addmedicine.html")


app.run(debug=True)
