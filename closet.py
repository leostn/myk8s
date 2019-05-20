# all the imports

import os
import sqlite3
import re
import time

import json
import urllib

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

os.environ['FLASK_APP'] = 'closet'

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , closet.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path,'user.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('closet_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db(schema='test_schema.sql'):
    db = get_db()
    with app.open_resource(schema, mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def weather_get():

    return 2

def cart2order(username,watchlistid):
    with sqlite3.connect('user.db') as con:
     cur = con.cursor()
     com="INSERT INTO ordernum (watchlist_id, username,status) values(?,?,?)"
     cur.execute(com,(watchlistid,username,"processing"))
     con.commit()

     cur = cur.execute(
         'select ordernum.order_id from ordernum where ordernum.watchlist_id=? and ordernum.username=?', (watchlistid, username))
     order_id = cur.fetchall()
     length=len(order_id)
     order_id=order_id[length-1][0]
     com = "INSERT INTO state (watchlist_id, username,productId,order_id) select kart.watchlist_id, kart.username, kart.productId,ordernum.order_id from kart, ordernum where kart.watchlist_id= ? and kart.username= ? and ordernum.watchlist_id= ? and ordernum.username= ? and ordernum.order_id= ? "
     cur.execute(com,(watchlistid,username,watchlistid,username,order_id))
     con.commit()


     cur.execute('Delete FROM kart where kart.watchlist_id= ? and kart.username=?',(watchlistid,username))
     con.commit()

     cur.fetchall()
     cur = cur.execute(
         'select * from state where state.watchlist_id=? and state.username=?',(watchlistid,username))
     watchlistsname = cur.fetchall()
     print(watchlistsname)
     cur.close()

@app.route('/')
def show_watchlists():
    watchlistsname = get_user_watchlistsname()
    return render_template('dashboard.html',showwatch=1,watchlistsname=watchlistsname)


def get_user_watchlistsname():
    db = get_db()
    auth_user = session.get("username")
    cur = db.execute(
        'select * from user_watchlists where user_watchlists.username = "%s"' % auth_user)
    watchlistsname = cur.fetchall()
    return watchlistsname

def get_user_watchlists_id(watchlistname):
    db = get_db()
    auth_user = session.get("username")

    cur = db.execute(
        'select * from user_watchlists where user_watchlists.username = ? and user_watchlists.watchlist_name = ?',[auth_user,watchlistname])
    watchlistsid = cur.fetchall()
    return watchlistsid

def getuserDetails(watchlistname,watchlistid):
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        if not session['logged_in']:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT count(productId) FROM kart WHERE watchlist_id = ? and firstName=? " ,[watchlistid,watchlistname])
            noOfItems = cur.fetchone()[0]
    conn.close()
    return (loggedIn, firstName, noOfItems)

def delete_watchlist_method(username,watchlistname,watchlistid):
    db = get_db()
    print(username,watchlistname,watchlistid)
    cur = db.execute(
        'DELETE FROM user_watchlists where user_watchlists.username=? and user_watchlists.firstName =? and user_watchlists.watchlist_id =?',
        [username,watchlistname,watchlistid])
    db.commit()
    cur.fetchall()
    cur = db.execute(
        'DELETE FROM kart where kart.username=? and kart.watchlist_id=? ',
        [username, watchlistid])
    db.commit()
    cur.fetchall()
    cur = db.execute(
        'DELETE FROM state where state.username=? and state.watchlist_id=? ',
        [username, watchlistid])
    db.commit()
    cur.fetchall()
    cur = db.execute(
        'DELETE FROM ordernum where ordernum.username=? and ordernum.watchlist_id=? ',
        [username, watchlistid])
    db.commit()
    cur.fetchall()
    cur.close()


@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    auth_user = session.get("username")
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        postcode = request.form['postcode']
        city = request.form['city']
        phone = request.form['phone']
        with sqlite3.connect('user.db') as con:
                try:
                    cur = con.cursor()
                    cur.execute('UPDATE user_watchlists SET email = ?,firstName = ?, lastName = ?, address1 = ?, postcode = ?, city = ?, phone = ? WHERE firstName = ? and username= ?', (email,firstName, lastName, address1, postcode, city, phone,firstName,auth_user))
                    con.commit()
                    msg = "Saved Successfully"
                except:
                    con.rollback()
                    msg = "Error occured"
        cur.execute('SELECT watchlist_id from user_watchlists WHERE firstName = ? and username= ?',
                    [firstName, auth_user])
        watchlistid = cur.fetchone()[0]
        con.commit()
        con.close()
        return render_template("ProfileHome.html",loggedIn=True, firstName=firstName,watchlistname=firstName,watchlistid=watchlistid)

def add_watchlistname(gender,email,firstName,lastName,address1,postcode,city,phone):
    auth_user = session.get("username")
    if not session['logged_in']:
        abort(401)
    db=get_db()
    db.execute("insert into user_watchlists(username,gender,email,firstName,lastName,address1,postcode,city,phone) values (?,?,?,?,?,?,?,?,?)", [auth_user, gender,email,firstName,lastName,address1,postcode,city,phone])
    db.commit()

def getnum(watchlistid):
    auth_user = session.get("username")
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT count(productId) FROM kart WHERE watchlist_id = ? and username= ?', [watchlistid,auth_user])
        noOfItems = cur.fetchone()[0]
    conn.close()
    return noOfItems

@app.route('/function', methods=['GET', 'POST'])
def function_select():
    if not session['logged_in']:
        abort(401)
    else:
        msg = request.args.get("name").split("_")
        watchlist_name=msg[0]
    return render_template("dashboard.html",showwatchlist=watchlist_name,showid=msg[1])

@app.route("/eshopping")
def eshopping():
    auth_user = session.get("username")
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid= meg[1]
    noOfItems = getnum(watchlistid)
    [teplow,tephigh,itemData,categoryDataM,categoryDataF]=pushclo(auth_user,watchlistid)
    itemData = parse(itemData)
    return render_template('shoppingpage.html',watchlistname=watchlistname,watchlistid=watchlistid,loggedIn=True, firstName=watchlistname, noOfItems=noOfItems,categoryDataM=categoryDataM,categoryDataF=categoryDataF,itemData=itemData,tephigh=tephigh,teplow=teplow)

def pushclo(auth_user,watchlistid):
    weather = weather_get()
    teplow = 1
    tephigh = 2
    tmp = 0
    for i in range(0, 7):

        tmp =24
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT gender FROM user_watchlists where user_watchlists.watchlist_id=? and user_watchlists.username=?  ',
            (watchlistid, auth_user))
        gender = cur.fetchall()
        if gender[0][0] == 'm':
            if tmp >= 25:
                cur.execute(
                    'SELECT productId, name, price, description, image, stock FROM products where products.state=? and products.gender=? and products.categoryId=? or products.categoryId=? or products.categoryId=?',
                    ('p', 'm', 1, 2, 6))
            else:
                cur.execute(
                    'SELECT productId, name, price, description, image, stock FROM products where products.state=? and products.gender=? and products.categoryId=?or products.categoryId=? or products.categoryId=? or products.categoryId=?',
                    ('p', 'm', 2, 4, 5, 6))
        else:
            if tmp >= 25:
                cur.execute(
                    'SELECT productId, name, price, description, image, stock FROM products where products.state=? and products.gender=? and products.categoryId=? or products.categoryId=? or products.categoryId=?',
                    ('p', 'm', 7, 8, 12))
            else:
                cur.execute(
                    'SELECT productId, name, price, description, image, stock FROM products where products.state=? and products.gender=? and products.categoryId=? or products.categoryId=? or products.categoryId=?',
                    ('p', 'm', 9, 10, 11))
        itemData = cur.fetchall()
        cur.execute('SELECT categoryId, type FROM categories where gender=?', ['m'])
        categoryDataM = cur.fetchall()
        cur.execute('SELECT categoryId, type FROM categories where gender=?', ['f'])
        categoryDataF = cur.fetchall()
    return teplow,tephigh,itemData,categoryDataM,categoryDataF


def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

@app.route('/addwatchlist', methods=['GET', 'POST'])
def add_watchlist():
    addwatchlist=1
    if not session['logged_in']:
        abort(401)
    else:
        if request.method == 'POST':
            gender=request.form['gender']
            email = request.form['email']
            firstName = request.form['firstName']
            lastName = request.form['lastName']
            address1 = request.form['address1']
            postcode = request.form['postcode']
            city = request.form['city']
            phone = request.form['phone']
            #addwatchlist = None
            add_watchlistname(gender, email, firstName, lastName, address1, postcode, city, phone)
            flash("add charactor succseess")

    watchlistsname = get_user_watchlistsname()
    print(watchlistsname)
    return render_template('dashboard.html',showwatch=1,watchlistsname=watchlistsname, addwathlist=addwatchlist)

@app.route("/addToCart")
def addToCart():
        auth_user = session.get("username")
        meg = request.args.get("name").split("_")
        watchlistname = meg[0]
        watchlistid = meg[1]
        productId = meg[3]

        with sqlite3.connect('user.db') as conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO kart (watchlist_id,username, productId) VALUES (?,?,?)", (watchlistid,auth_user, productId))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occured"
            cur = conn.cursor()
        conn.close()
        noOfItems = getnum(watchlistid)
        [teplow, tephigh, itemData, categoryDataM, categoryDataF] = pushclo(auth_user, watchlistid)
        itemData = parse(itemData)
        return render_template('shoppingpage.html', watchlistname=watchlistname, watchlistid=watchlistid, loggedIn=True,
                               firstName=watchlistname, noOfItems=noOfItems, categoryDataM=categoryDataM,
                               categoryDataF=categoryDataF, itemData=itemData, tephigh=tephigh,
                               teplow=teplow)


@app.route("/cart")
def cart():
    auth_user = session.get("username")
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid = meg[1]
    noOfItems = getnum(watchlistid)
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT products.productId, products.name, products.price, products.image,kart.items_id FROM products, kart WHERE products.productId = kart.productId AND kart.watchlist_id = ? and kart.username=? ',[watchlistid,auth_user])
        products = cur.fetchall()
    totalPrice = 0
    conn.close()
    for row in products:
        totalPrice += row[2]
    return render_template("shopcart.html", products = products, totalPrice=totalPrice, loggedIn=True, firstName=watchlistname, noOfItems=noOfItems,watchlistname=watchlistname,watchlistid=watchlistid)

@app.route("/account/orders")
def myorder():
    auth_user = session.get("username")
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid = meg[1]
    noOfItems = getnum(watchlistid)
    if len(meg)==2:
        with sqlite3.connect('user.db') as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT ordernum.order_id FROM ordernum WHERE ordernum.watchlist_id = ? and ordernum.username= ? order by ordernum.order_id  desc',
                [watchlistid, auth_user])
            orderid = cur.fetchall()
        conn.close()
        return render_template("myorder.html", loggedIn=True,firstName=watchlistname, noOfItems=noOfItems, watchlistname=watchlistname,
                               watchlistid=watchlistid,orderid=orderid)
    else:
        orderid=meg[2]
        with sqlite3.connect('user.db') as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT products.productId, products.name, products.price, products.image,ordernum.status, ordernum.order_id FROM products, state,ordernum WHERE ordernum.watchlist_id=state.watchlist_id and  ordernum.username=state.username and ordernum.username=state.username and products.productId=state.productId and ordernum.order_id = state.order_id and ordernum.watchlist_id= ? and ordernum.username=? AND ordernum.order_id= ? ',
                [watchlistid, auth_user,int(orderid)])
            products = cur.fetchall()
        conn.close()
        totalPrice=0
        for row in products:
                 totalPrice += row[2]
                 status=row[4]
        return render_template("myorder.html", products=products,totalPrice=totalPrice, loggedIn=True,
                               firstName=watchlistname, noOfItems=noOfItems, watchlistname=watchlistname,
                               watchlistid=watchlistid,a=int(orderid),status=status)

@app.route("/removeFromCart")
def removeFromCart():
    auth_user = session.get("username")
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid = meg[1]
    productId = meg[3]
    itemid = meg[5]
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        try:
            cur.execute('DELETE FROM kart WHERE watchlist_id = ? AND username = ? AND productId = ? and items_id=?',[watchlistid,auth_user,productId,itemid])
            conn.commit()
            msg = "removed successfully"
        except:
            conn.rollback()
            msg = "error occured"
    conn.close()
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT products.productId, products.name, products.price, products.image,kart.items_id FROM products, kart WHERE products.productId = kart.productId AND kart.watchlist_id = ? and kart.username=? ',
            [watchlistid, auth_user])
        products = cur.fetchall()
        print(products)
        totalPrice = 0
        for row in products:
         totalPrice += row[2]
    conn.close()
    noOfItems = getnum(watchlistid)
    return render_template("shopcart.html", products=products, totalPrice=totalPrice, loggedIn=True,
                               firstName=watchlistname, noOfItems=noOfItems, watchlistname=watchlistname,
                               watchlistid=watchlistid)

@app.route('/feedback',methods=['GET', 'POST'])
def feedback():
    return render_template("feedback.html")

@app.route('/deletewatchlist', methods=['GET', 'POST'])
def delete_watchlist():
    if not session['logged_in']:
        abort(401)
    meg = request.args.get("name").split("_")
    watchlistname=meg[1]
    watchlistid=meg[2]
    delete_watchlist_method(session['username'], watchlistname,watchlistid)
    flash("delete watch list Success!")
    watchlistsname = get_user_watchlistsname()
    return render_template("dashboard.html",showwatch=1, watchlistsname=watchlistsname)

@app.route("/productDescription")
def productDescription():
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid = meg[1]
    productId = meg[3]
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ' + productId)
        productData = cur.fetchone()
    conn.close()
    noOfItems=getnum(watchlistid)
    return render_template("productDescription.html", data=productData, loggedIn = True, firstName = watchlistname,noOfItems=noOfItems, watchlistid=watchlistid,productId=productId,watchlistname=watchlistname)

@app.route("/displayCategory")
def displayCategory():
        meg = request.args.get("name").split("_")
        watchlistname = meg[0]
        watchlistid = meg[1]
        categoryId = meg[3]
        with sqlite3.connect('user.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT products.productId, products.name, products.price, products.image, categories.type FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = " + categoryId)
            data = cur.fetchall()
        conn.close()
        categoryName = data[0][4]
        data = parse(data)
        num = getnum(watchlistid)
        return render_template('displayCategory.html',data=data, loggedIn=True, firstName=watchlistname, noOfItems=num, categoryName=categoryName,watchlistid=watchlistid,watchlistname=watchlistname)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        passw = request.form['password']
        if user and passw:
            db = get_db()
            cur = db.execute("select *  from users where username =? and password=?", [user, passw])
            rows = cur.fetchone()
            cur2 = db.execute("select username  from users")
            rows2 = cur2.fetchone()
            if rows:
                session['logged_in'] = True
                session['username'] = user
                flash("Login Success!")
                watchlistsname = get_user_watchlistsname()
                return render_template('dashboard.html',showwatch=1,watchlistsname=watchlistsname)
            elif user not in rows2:
              error = 'User not registered'
            else:
              error = 'Incorrect username or password'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    time.sleep(1)
    return redirect(url_for('show_watchlists'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    users = [dict(username=row[0], password=row[1]) for row in get_db().execute('select username, password from users order by username desc').fetchall()]
    registeredmembers=[]
    for i in users:
        registeredmembers.append(i['username'])
    if request.method == 'POST':
        user = request.form['username']
        passw = request.form['password']

        cfm_passw = request.form['cfm_password']
        if user in registeredmembers:
            error = 'User already registered'
        elif passw != cfm_passw:
            error = 'Passwords do not match'
        elif len(passw) < 8:
            error = 'Invalid password. Passwords must contain at least 8 characters, and at least one capital letter and number'
        elif not re.search("[0-9]", passw):
            error = 'Invalid password. Passwords must contain at least 8 characters, and at least one capital letter and number'
        elif not re.search("[A-Z]", passw):
            error = 'Invalid password. Passwords must contain at least 8 characters, and at least one capital letter and number'
        else:
            get_db().execute('insert into users (username, password) values (?, ?)', [user, passw])
            get_db().commit()
            flash('You were successfully registered')
            return redirect("login")
    return render_template('register.html', error=error)

@app.route("/account/profile/edit")
def editProfile():
    with sqlite3.connect('user.db') as conn:
        meg = request.args.get("name").split("_")
        watchlistname = meg[0]
        watchlistid = meg[1]
        print(watchlistname,watchlistid)
        cur = conn.cursor()
        cur.execute("SELECT email, firstName, lastName, address1,postcode, city,  phone FROM user_watchlists WHERE watchlist_id = ?",[watchlistid])
        profileData = cur.fetchone()

    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=True, firstName=watchlistname,watchlistname=watchlistname,watchlistid=watchlistid)


@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    auth_user = session.get("username")
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid = meg[1]
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        newPassword = request.form['newpassword']
        print(auth_user,oldPassword,newPassword)
        with sqlite3.connect('user.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username = ? ",[auth_user])
            password = cur.fetchone()[0]
            if len(newPassword) < 8:
                error = 'Invalid password. Passwords must contain at least 8 characters, and at least one capital letter and number'
            elif not re.search("[0-9]", newPassword):
                 error = 'Invalid password. Passwords must contain at least 8 characters, and at least one capital letter and number'
            elif not re.search("[A-Z]", newPassword):
                  error = 'Invalid password. Passwords must contain at least 8 characters, and at least one capital letter and number'
            elif (password == oldPassword):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE username = ?", (newPassword, auth_user))
                    conn.commit()
                    msg="Changed successfully"
                except:
                    conn.rollback()
                    msg = "Failed"
                session.pop('logged_in', None)
                flash('You were logged out')
                time.sleep(1)
                return redirect(url_for('show_watchlists'))
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg,watchlistname=watchlistname,watchlistid=watchlistid)
    else:
        return render_template("changePassword.html",watchlistname=watchlistname,watchlistid=watchlistid)

@app.route("/account/profile")
def profileHome():
    meg = request.args.get("name").split("_")
    watchlistname = meg[0]
    watchlistid = meg[1]
    return render_template("profileHome.html", watchlistname=watchlistname,watchlistid = watchlistid,loggedIn=True, firstName=watchlistname)

@app.route("/search", methods=["GET", "POST"])
def search():
    meg = request.args.getlist("aa")[0].split('_')
    watchlistname = meg[0]
    watchlistid = meg[1]
    keyword=request.args.getlist("keyword")[0]
    keyword=str(keyword)
    with sqlite3.connect('user.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT products.productId, products.name, products.price, products.image FROM products WHERE products.name like '%"+keyword+"%' or products.description like '%"+keyword+"%'")
        data = cur.fetchall()
        print(data)
        print(1)
        if not data:
            cur.execute(
                "SELECT categories.type,categories.categoryId FROM categories WHERE  categories.type like '%"+keyword+"%'")
            cate = cur.fetchall()
            print(cate)
            for row in cate:
                print(row[1])
                cur.execute(
                 "SELECT products.productId, products.name, products.price, products.image FROM products WHERE products.categoryId= ? ",(str(row[1])))
                data = data+cur.fetchall()
    conn.close()
    data = parse(data)
    num = getnum(watchlistid)
    return render_template('search.html', data=data, loggedIn=True, firstName=watchlistname, noOfItems=num,
                           searchName=keyword, watchlistid=watchlistid, watchlistname=watchlistname)

@app.route('/checkout')
def checkout():
    meg = request.args.get("name").split('_')
    watchlistname = meg[0]
    watchlistid = meg[1]
    auth_user = session.get("username")
    noOfItems = getnum(watchlistid)
    if noOfItems:
        cart2order(auth_user,watchlistid)
        [teplow, tephigh, itemData, categoryDataM, categoryDataF] = pushclo(auth_user, watchlistid)
        itemData = parse(itemData)
        return render_template('shoppingpage.html', watchlistname=watchlistname, watchlistid=watchlistid, loggedIn=True,
                               firstName=watchlistname, noOfItems=0, categoryDataM=categoryDataM,
                               categoryDataF=categoryDataF, itemData=itemData, tephigh=tephigh, teplow=teplow)
    else:
        error='choose production first'
        return render_template("shopcart.html",  totalPrice=0, loggedIn=True,
                               firstName=watchlistname, noOfItems=noOfItems, watchlistname=watchlistname,
                               watchlistid=watchlistid,error=error)


@app.route('/shutdown')
def shutdown():
    if app.environment == 'test':
        shutdown_server()
    return "Server shutdown"

@app.route("/registerationForm")
def registrationForm():
        return render_template("add_user.html")

@app.cli.command('start')

def start():
    app.config.from_object(__name__) # load config from this file

    app.config.update(dict(
        DATABASE=os.path.join(app.root_path, 'uese.db'),
        SECRET_KEY='Production key',
    ))
    app.config.from_envvar('closet_SETTINGS',  silent=True)
    app.run(port=5003)


def test_server():
    ### Setup for integration testing
    app.config.from_object(__name__) # load config from this file

    app.config.update(dict(
        DATABASE=os.path.join(app.root_path, 'user.db'),
        SECRET_KEY='Test key',
        SERVER_NAME='localhost:5000',
        # DEBUG=True, # does not work from behave
    ))
    app.config.from_envvar('closet_TEST_SETTINGS',  silent=True)
    app.environment = 'test'
    with app.app_context():
        init_db('test_schema.sql')
    app.run()


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError("Not running with Werkzeug server")
    if app.environment == 'test':
        func()
        os.unlink(app.config['DATABASE'])

if __name__ == '__main__':
    app.run()


