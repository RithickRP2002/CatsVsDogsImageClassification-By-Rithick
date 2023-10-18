import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request, redirect, url_for, session
from keras.models import load_model
from keras.preprocessing import image
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re, secrets

app = Flask(__name__)

app.secret_key = secrets.token_hex(16)

dic = {0 : 'Cat', 1 : 'Dog'}

model = load_model('my_model.h5')

def predict_label(img_path):
    i = image.load_img(img_path, target_size=(100, 100))
    i = image.img_to_array(i) / 255.0
    i = np.expand_dims(i, axis=0)
    p = model.predict(i)
    return dic[np.argmax(p)]

# db
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "rithick"
app.config['MYSQL_PASSWORD'] = "dell2002ros"
app.config['MYSQL_DB'] = "cvd"

mysql = MySQL(app)

@app.route("/", methods=['GET', 'POST'])
def main():
    return render_template("login.html")

# routes login
@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s AND password = % s', (email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            return render_template('index.html')
        else:
            msg = 'Please enter correct email / password !'
    return render_template('login.html', msg = msg)
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))
  
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form :
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not userName or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user VALUES (NULL, % s, % s, % s)', (userName, email, password, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)

# routes main

@app.route("/submit", methods=['GET', 'POST'])
def get_output():
    if request.method == 'POST':
        img = request.files['my_image']

        img_path = "static/" + img.filename
        img.save(img_path)

        p = predict_label(img_path)


        userid = session.get('userid', None)

        if userid is not None:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO predictions (image, result, userid) VALUES (%s, %s, %s)", (img_path, p, userid))
            mysql.connection.commit()
            cur.close()

        return render_template("index.html", prediction=p, img_path=img_path)

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
