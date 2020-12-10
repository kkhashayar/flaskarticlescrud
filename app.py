from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
#-- from data import Articles #-- dummy data
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

app.config["SECRET_KEY"] = "secretkey"
#-- Config mysql
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "debian-sys-maint"
app.config["MYSQL_PASSWORD"] = "BF4VdktqPcsBvYGn"
app.config["MYSQL_DB"] = "myflaskapp"
#-- returns quesries as dictionary like JS object
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
#-- Initialize MYSQL
mysql = MySQL(app)

""" Installing mysql server and client on linux-unix based machine(DEB)

    ###############
        host     = localhost
        user     = debian-sys-maint
        password = BF4VdktqPcsBvYGn
        socket   = /var/run/mysqld/mysqld.sock
        [mysql_upgrade]
        host     = localhost
        user     = debian-sys-maint
        password = BF4VdktqPcsBvYGn
        socket   = /var/run/mysqld/mysqld.sock
    ###############

    apt-get install mysql-server
    apt-get install libmysqlclient-dev
    mysql -u root debian-sys-maint (username) -p (password) "BF4VdktqPcsBvYGn"
    SHOW DATABASES;
    CREATE DATABASE database-name;
    USE database-name;

    CREATE TABLE table-name(id INT(11) AUTO INCREMENT PRIMATY KEY,
                           (name VARCHAR(100),
                           (email VARCHARD(100),
                           (username VARCHAR(30),
                           (password VARCHAR(100),
                           (register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    SHOW TABLES;
    DESCRIBE table-name;

    to communicate with mysql database with flask:
        pip3 install flask-mysqldb or python3 -m pip install flask-mysqldb

    for forms:
        flask-WTF
        pip3 install flask-WTF or python3 -m pip install flask-WTF

    to hash the passwords:
        pip3 install passlib or python3 -m pip install passlib
"""

"""
    Classes to use wtforms.
    in _formhelpers.html checkout whats the macros!?
"""
class RegisterForm(Form):
    name = StringField("Name", [validators.Length(min=4, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField("Password",[
        validators.DataRequired(),
        validators.EqualTo("confirm", message="Passwords do not match")])
    confirm = PasswordField("Confirm Password")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        #-- getting data values from _forms
        name = form.name.data
        email = form.email.data
        username = form.username.data
        #-- Encrypt the password before submit
        password = sha256_crypt.encrypt(str(form.password.data))
        #-- test the forms values
        #--print("Name: {}, email: {}, username: {}, password: {}".format(name, email, username, password))

        cur = mysql.connection.cursor()

        #-- basic datacheck with email K version!
        cur.execute("SELECT * from users WHERE email = %s", (email,))
        result = cur.fetchone()
        if result != None:
            cur.close()
            flash("Change your inputs", "danger")
            return redirect(url_for("home"))

        #-- if email doesnt exists then we insert a new record into database
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",(name, email,username, password))
        #-- commit to DB
        mysql.connection.commit()
        #-- Close the connection
        cur.close()

        #-- initialize the flash messaging message, categury
        flash("you registered", "success")
        return redirect(url_for("home"))

    return render_template("register.html", form=form)


#------------------------ Dummy data
#-- Articles = Articles() #-- referring to returned data from data file


#-- User login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        #-- get data from _forms
        #-- we use normal html forms not WTFORMS
        username = request.form["username"]
        #-- we will do datacheck, password from form and password from database
        password_candidate = request.form["password"]
        #-- create cursor
        cur = mysql.connection.cursor()
        #-- grt user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #-- Get stored Hash
            data = cur.fetchone()
            password = data["password"]
            #--compare the passfors (datacheck)
            if sha256_crypt.verify(password_candidate, password):
                #-- Awesome feature to print on console, instead of using classic print!
                #--app.logger.info("PASSWORD MATCHED")
                #-- create a session
                session["logged_in"] = True
                session["username"] = username
                flash("you logged in", "success")
                return redirect(url_for("dashboard"))
                cur.close()
            else:
                error = "Invalid login"
                return render_template("login.html", error=error)

        else:
            error = "Username not found"
            return render_template("login.html", error=error)
    #-- Get request!
    return render_template("login.html")

#-- Check for session (login) route protections
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please login", "danger")
            return redirect(url_for("login"))
    return wrap

#-- Logout
@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("you logged out!", "success")
    return redirect(url_for("login"))



#------------------------ ROUTES
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


#-- List of articles
@app.route("/articles")
def articles():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    #-- If there is one
    if result >0:
        return render_template("articles.html", articles=articles)
    #-- if there is nothing flashing user
    else:
        msg = "No Articles Found"
        return render_template("articles.html", msg=msg)
    cur.close()



@app.route("/article/<string:id>/")
@is_logged_in
def article(id):
    #-- query based on id
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()
    cur.close()
    return render_template("article.html", article=article)


#-- Dashboard
#-- link to add articles, list of the articles for current user!
@app.route("/dashboard")
@is_logged_in #-- without parentheses and argument
def dashboard():
    #-- getting all articles
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    #-- If there is one
    if result >0:
        return render_template("dashboard.html", articles=articles)
    #-- if there is nothing flashing user
    else:
        #msg = "No Articles Found"
        return render_template("dashboard.html")
    cur.close()

#################### ADDING ARTICLE
"""
WTFORMS class for articles
one of the solutions to have editor on the page is CKEditor
we can download it or use the script tag and use the CDN version :
1)
at the buttom of the page after bootstrap link
    <script src="//cdn.ckeditor.com/4.15.1/standard/ckeditor.js"></script>

2)
and we have to add acript tag and overide the editor by:
        <script type="text/javascript">
        CKEDITOR.replace("editor")
        </script>
3)
in add_article or any page needed, in the render_field after class_="form-control", here:
    add id="editor"
"""
class ArticleForm(Form):
    title = StringField("Title", [validators.Length(min=4, max=250)])
    body = TextAreaField("Body", [validators.Length(min=30)])

@app.route("/add_article", methods=["POST", "GET"])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        #-- Create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s,%s,%s)",(title, body, session["username"]))
        mysql.connection.commit()
        cur.close()

        flash("Article created", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_article.html", form=form)


#--Edit article
@app.route("/edit_article/<string:id>", methods=["POST", "GET"])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()

    #-- get Article by ID
    result = cur.execute("SELECT * FROM articles WHERE id = %s ",[id])
    article = cur.fetchone()

    # using the same form but we have to populate the fields
    form = ArticleForm(request.form)

    form.title.data = article["title"]
    form.body.data = article["body"]

    if request.method == "POST" and form.validate():
        #-- this two field should come from the form
        title = request.form["title"]
        body = request.form["body"]

        #-- Create cursor
        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))

        mysql.connection.commit()
        cur.close()

        flash("Article Updates", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_article.html", form=form)

#-- delete article
@app.route("/delete_article/<string:id>", methods=["POST"])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id=%s",[id])
    mysql.connection.commit()
    cur.close()
    flash("Article deleted", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=False)
