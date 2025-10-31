# Import 'render_template' to render HTML files from the 'templates' folder
from flask import Flask,render_template,request,redirect,session,flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__,
                )
    
    # 1.2 Load configuration from 'config.py'
    
    app.config.from_pyfile('config.py')
    return app

app = create_app()
db = SQLAlchemy() #INITIALIZATION
db.init_app(app) #integration
migrate = Migrate(app, db)



#Database

#every table in the database is a class here


class Role(db.Model):
    rid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    role_name=db.Column(db.String,unique=True,nullable=False)
    description=db.Column(db.String,nullable=True)

class User(db.Model):
    uid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    email=db.Column(db.String,unique=True,nullable=False)
    password=db.Column(db.String,nullable=False)
    f_rid = db.Column(db.Integer,db.ForeignKey(Role.rid),nullable=False)
    roles=db.relationship(Role,backref='users',lazy=True)

class Theatre(db.Model):
    tid=db.Column(db.Integer,primary_key=True,autoincrement=True)
    theatre_name=db.Column(db.String,unique=True,nullable=False)
    location=db.Column(db.String,nullable=False)
    franchise=db.Column(db.String,nullable=False)
    u_id=db.Column(db.Integer,db.ForeignKey(User.uid),nullable=False)
    user = db.relationship(User,backref='theatre',lazy=True)   
    
# <User x>.roles ---> <Role x>
# <Role y>.users --> [<User x>, <User y>, ...]

#User1 email1 pass1 roleid1
#User2 email2 pass2 roleid1

@app.route("/")
def landing_page():
    users = User.query.all()
    return render_template("index.html")

@app.route("/login",methods=['GET','POST'])
def login_page():
    if request.method=='GET':
        return render_template("login.html")
    else:
        form_email = request.form.get("email")
        form_password = request.form.get("password")
        #Check if user exists
        check_user = User.query.filter_by(email=form_email).first()
        if check_user:
            if check_user.password == form_password:
                print("Login Successful going to dashboard")
                flash("Login Successful")
                session['email'] = form_email
                session['f_rid'] = check_user.f_rid
                return redirect("/dashboard")
            else:
                print("Incorrect Password")
                flash("Incorrect Password")
                return redirect("/login")
        else:
            print("User does not exist")
            flash("User does not exist please signup")
            return redirect("/signup")

            

@app.route("/signup",methods=['GET','POST'])
def signup_page():
    if request.method=='GET':
        return render_template("signup.html")
    else:
        form_email=request.form.get("email")
        form_password=request.form.get("password")

        check_user=User.query.filter_by(email=form_email).first()

        if check_user:
            print("User already exists, please login")
            flash("User already exists, please login")
            return redirect("/login")
        else:
            new_user = User(
                email = form_email,
                password = form_password,
                f_rid = 2 #default role as customer
            )
            db.session.add(new_user)
            db.session.commit()
            print("User created successfully, please login")
            flash("User created successfully, please login")
            return redirect("/login")
        
@app.route("/dashboard")
def dashboard_page():
    jinjaemail = session.get("email")
    role = session.get("f_rid")
    if role == 1:
        theatres = Theatre.query.all()
        users = User.query.all()
        return render_template("AdminDashboard.html",jinjaemail=jinjaemail,theatres=theatres,users=users)
    if role == 2:
        return render_template("Dashboard.html",jinjaemail=jinjaemail)

def create_roles():
    check_admin = Role.query.filter_by(role_name="Admin").first()
    if not check_admin:
        admin_role = Role(
            role_name = "Admin",
            description = "Administrator or superuser"
        )
        db.session.add(admin_role)
        db.session.commit()
    check_customer = Role.query.filter_by(role_name="Customer").first()
    if not check_customer:
        customer_role = Role(
            role_name = "Customer",
            description = "customer"
        )
        db.session.add(customer_role)
        db.session.commit()
    check_theatre = Role.query.filter_by(role_name="Theatre").first()
    if check_theatre is None:
        theatre_role = Role(
            role_name = "Theatre",
            description = "theatre owner"
        )
        db.session.add(theatre_role)
        db.session.commit()

def auto_admin_creation():
    check_admin_user = User.query.filter_by(email="Admin@gmail.com",f_rid=1).first()
    if not check_admin_user:
        admin_user = User(
            email="Admin@gmail.com",
            password="Admin@123",
            f_rid=1
        )
        db.session.add(admin_user)
        db.session.commit()

@app.route('/create_theatre',methods=['GET','POST'])
def create_theatre():
    if request.method=='GET':
        return render_template("create_theatre.html")
    else:
        theatre_email = request.form.get("theatre_email")
        theatre_password = request.form.get("theatre_password")
        theatre_name = request.form.get("theatre_name")
        theatre_location = request.form.get("theatre_location")
        theatre_franchise = request.form.get("theatre_franchise")

        check_user = User.query.filter_by(email=theatre_email).first()

        if not check_user:
            new_theatre_user = User(email=theatre_email,
                                    password=theatre_password,
                                    f_rid=3)
            db.session.add(new_theatre_user)
            db.session.commit()

            new_theatre = Theatre(
                theatre_name=theatre_name,
                location=theatre_location,
                franchise=theatre_franchise,
                u_id=new_theatre_user.uid
            )
            db.session.add(new_theatre)
            db.session.commit()
            flash("Theatre created successfully")
            return redirect("/dashboard")
        
        else:
            print("User with this email already exists")
            flash("User with this email already exists")
            return redirect("/create_theatre")

@app.route('/edit_theatre/<argtid>',methods=['GET','POST'])
def edit_theatre(argtid):
    if request.method=="GET":
        current_theatre = Theatre.query.filter_by(tid=argtid).first()
        return render_template("edit_theatre.html",jinjacurrent_theatre=current_theatre)
    else:
        new_theatre_name = request.form.get("theatre_name")
        new_theatre_location = request.form.get("theatre_location")
        new_theatre_franchise = request.form.get("theatre_franchise")
        
        current_theatre = Theatre.query.filter_by(tid=argtid).first()
        check_theatre = Theatre.query.filter_by(theatre_name=new_theatre_name).first()
        if check_theatre and str(check_theatre.tid)==argtid:
            current_theatre.location = new_theatre_location
            current_theatre.franchise = new_theatre_franchise
            db.session.commit()
            flash("Theatre details updated successfully")
            return redirect("/dashboard")
        if not check_theatre:
            current_theatre.theatre_name = new_theatre_name
            current_theatre.location = new_theatre_location
            current_theatre.franchise = new_theatre_franchise
            db.session.commit()
            flash("Theatre details updated successfully")
            return redirect("/dashboard")
        if check_theatre and str(check_theatre.tid)!=argtid:
            flash("Theatre name already exists, please choose a different name")
            return redirect(f"/edit_theatre/{argtid}")

@app.route('/delete_theatre/<argtid>',methods=['GET'])
def delete_theatre(argtid):
    current_theatre = Theatre.query.filter_by(tid=argtid).first()
    current_user = User.query.filter_by(uid=current_theatre.u_id).first()
    db.session.delete(current_theatre)
    db.session.delete(current_user)
    db.session.commit()
    flash("Theatre deleted successfully")
    return redirect("/dashboard")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_roles()
        auto_admin_creation()
    app.run(
        debug=True,
    )