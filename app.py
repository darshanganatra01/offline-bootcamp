# Import 'render_template' to render HTML files from the 'templates' folder
from flask import Flask,render_template,request,redirect,session

def create_app():
    app = Flask(__name__,
                )
    
    # 1.2 Load configuration from 'config.py'
    
    app.config.from_pyfile('config.py')
    return app

app = create_app()

@app.route("/")
def landing_page():
    return render_template("index.html")

@app.route("/login",methods=['GET','POST'])
def login_page():
    if request.method=='GET':
        return render_template("login.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        session["email"]=email
        return redirect("/dashboard")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")


@app.route("/dashboard")
def dashboard_page():
    jinjaemail = session.get("email")
    return render_template("Dashboard.html",jinjaemail=jinjaemail)


#/login the login page 
#/sigup the signup page1

#routes 


if __name__ == '__main__':
    print("--- Flask App Starting ---")
    print("--- Loading configuration from config.py ---")
    print("--- Looking for templates in the 'templates' folder ---")
    print("--- Access in your browser at: http://127.0.0.1:5001/ ---")
    app.run(
        debug=True,
    )