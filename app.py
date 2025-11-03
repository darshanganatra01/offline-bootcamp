# Import 'render_template' to render HTML files from the 'templates' folder
from flask import Flask,render_template,request,redirect,session,flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import date, timedelta
from datetime import date, timedelta, time, datetime
from flask import render_template, request, redirect, url_for, flash, session

# --- Define your 4 fixed slot times ---
# We use a dictionary:
# Key: The string for display and form values
# Value: The datetime.time object for the database


# import datetime at top of file
from datetime import date, datetime, timedelta, time

# Example slot definitions (adjust to your theatre times)
# Keys are canonical time strings 'HH:MM' (24-hour) — used in values and DB logic.
SLOT_TIME_OBJECTS = {
    "09:00": time(9, 0),
    "12:00": time(12, 0),
    "15:00": time(15, 0),
    "18:00": time(18, 0),
}
#[4,5,6,7,8,9,0]
# Human-friendly display labels
SLOT_LABELS = {
    "09:00": "09:00 AM",
    "12:00": "12:00 PM",
    "15:00": "03:00 PM",
    "18:00": "06:00 PM",
}


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

# --- New models: slot availability and bookings --- #

class Booking(db.Model):
    bid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    u_id = db.Column(db.Integer, db.ForeignKey(User.uid), nullable=True)
    t_id = db.Column(db.Integer, db.ForeignKey(Theatre.tid), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    booking_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String, nullable=False, default='Available')    #Availablle,Booked,Canceled,Completed

    user = db.relationship(User, backref='bookings', lazy=True)
    theatre = db.relationship(Theatre, backref='bookings', lazy=True)


class CompletedBooking(db.Model):
    cbid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bid = db.Column(db.Integer, db.ForeignKey(Booking.bid), nullable=False)
    review = db.Column(db.String, nullable=True)

    booking = db.relationship(Booking, backref='completed_booking', lazy=True)


#When The Theatre will make the slots available for booking we are going to create the enteries in booking table
#By makig the status available and when booked from the user i want to update and show




#<CompletedBooking x>.booking = <Booking y>
# <Booking y>.user ===> <User z>
# <Booking y>.theatre ===> <Theatre p>





# <User x>.roles ---> <Role x>
# <Role y>.users --> [<User x>, <User y>, ...]

#User1 email1 pass1 roleid1
#User2 email2 pass2 roleid1

@app.route("/manage-slots", methods=["GET", "POST"])
def manage_slots_page():
    # --- Authentication ---
    jinjaemail = session.get("email")
    role = session.get("f_rid")
    if role != 3:
        flash("You do not have permission to view this page.", "error")
        return redirect(url_for("dashboard_page"))

    current_user = User.query.filter_by(email=jinjaemail).first()
    current_theatre = Theatre.query.filter_by(u_id=current_user.uid).first()
    if not current_theatre:
        flash("No theatre found for your account.", "error")
        return redirect(url_for("dashboard_page"))
    tid = current_theatre.tid

    # --- Date Logic (next 7 days starting tomorrow) ---
    start_date = date.today() + timedelta(days=1)
    end_date = start_date + timedelta(days=6)   # 7 days total: start_date .. start_date+6

    if request.method == "POST":
        # 1. Read checked boxes: values are "YYYY-MM-DD|HH:MM"
        checked_slots_from_form = request.form.getlist("slots")

        # Build desired set of canonical keys
        wanted_set = set()
        for v in checked_slots_from_form:
            try:
                date_str, time_str = v.split("|")
                slot_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                # Add only if in our allowed set
                if time_str in SLOT_TIME_OBJECTS and start_date <= slot_date <= end_date:
                    key = f"{slot_date.strftime('%Y-%m-%d')}|{time_str}"
                    wanted_set.add(key)
            except ValueError:
                continue  # ignore malformed values

        # 2. Fetch existing slots in DB for the theatre and date-range
        existing_db_slots = Booking.query.filter(
            Booking.t_id == tid,
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date
        ).all()

        print(wanted_set)


        # 3. Build existing set of canonical keys
        existing_set = set()
        existing_map = {}  # also maintain map if you want to inspect objects here
        for s in existing_db_slots:
            key = f"{s.booking_date.strftime('%Y-%m-%d')}|{s.booking_time.strftime('%H:%M')}"
            existing_set.add(key)
            existing_map[key] = s


        print(existing_set)

        # 4. Slots to create = wanted - existing
        to_create = wanted_set - existing_set

        print(to_create)


        if not to_create:
            flash("No new slots were selected to add.", "info")
        else:
            for key in to_create:
                date_part, time_part = key.split("|")
                booking_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                booking_time = SLOT_TIME_OBJECTS.get(time_part)
                if booking_time is None:
                    continue
                # create available slot
                new_slot = Booking(t_id=tid, booking_date=booking_date, booking_time=booking_time, status='Available')
                db.session.add(new_slot)
            try:
                db.session.commit()
                flash(f"Successfully added {len(to_create)} new slots!", "success")
            except Exception as e:
                db.session.rollback()
                flash("There was a database error while adding slots.", "error")

        return redirect(url_for("manage_slots_page"))

    # --- GET: prepare page data ---
    all_7_dates = [start_date + timedelta(days=i) for i in range(7)]

    existing_slots_db = Booking.query.filter(
        Booking.t_id == tid,
        Booking.booking_date >= start_date,
        Booking.booking_date <= end_date
    ).all()

    # Build a map of canonical_key -> slot_object for template
    existing_slots_map = {}
    for slot in existing_slots_db:
        key = f"{slot.booking_date.strftime('%Y-%m-%d')}|{slot.booking_time.strftime('%H:%M')}"
        existing_slots_map[key] = slot
    
    print(SLOT_LABELS)
    print(all_7_dates)
    print(existing_slots_map)

    return render_template(
        "manage_slots.html",
        jinjaemail=jinjaemail,
        dates=all_7_dates,
        slot_labels=SLOT_LABELS,             # label map: 'HH:MM' -> '09:00 AM'
        slot_times=SLOT_TIME_OBJECTS,        # time map: 'HH:MM' -> datetime.time(...)
        existing_slots_map=existing_slots_map,
        current_theatre=current_theatre
    )


@app.route("/cancel-slot/<int:booking_id>", methods=["POST"])
def cancel_slot(booking_id):
    # Authentication
    jinjaemail = session.get("email")
    role = session.get("f_rid")
    if role != 3:
        flash("You are not authorized.", "error")
        return redirect(url_for("dashboard_page"))

    current_user = User.query.filter_by(email=jinjaemail).first()
    current_theatre = Theatre.query.filter_by(u_id=current_user.uid).first()

    slot_to_cancel = Booking.query.get(booking_id)
    if not slot_to_cancel:
        flash("Slot not found.", "error")
        return redirect(url_for("manage_slots_page"))

    if not current_theatre or slot_to_cancel.t_id != current_theatre.tid:
        flash("This slot does not belong to your theatre.", "error")
        return redirect(url_for("manage_slots_page"))

    if slot_to_cancel.status == 'Booked':
        flash("Cannot cancel a slot that is already booked.", "warning")
        return redirect(url_for("manage_slots_page"))

    if slot_to_cancel.status == 'Available':
        try:
            db.session.delete(slot_to_cancel)
            db.session.commit()
            flash("Available slot has been cancelled.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error cancelling slot.", "error")
        return redirect(url_for("manage_slots_page"))

    # for other statuses (Canceled, Completed etc.)
    flash("Slot could not be cancelled.", "error")
    return redirect(url_for("manage_slots_page"))





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
        import os
        import matplotlib
        matplotlib.use('Agg') 
        import matplotlib.pyplot as plt
         # --- Query data ---
        theatres = Theatre.query.all()
        users = User.query.all()
        bookings = Booking.query.all()

        # Create /static/graphs folder if not exists
        graphs_path = os.path.join(app.root_path, 'static', 'graphs')
        os.makedirs(graphs_path, exist_ok=True)

        # ---------------------------------------------------------------------
        # 1️⃣ Graph: Number of Users by Role
        # ---------------------------------------------------------------------
        roles = Role.query.all()
        role_names = [r.role_name for r in roles]
        role_counts = [User.query.filter_by(f_rid=r.rid).count() for r in roles]

        plt.figure(figsize=(5, 4))
        plt.bar(role_names, role_counts)
        plt.title("Users by Role")
        plt.xlabel("Role")
        plt.ylabel("Count")
        users_by_role_path = os.path.join(graphs_path, "users_by_role.png")
        plt.savefig(users_by_role_path)
        plt.close()

        # ---------------------------------------------------------------------
        # 2️⃣ Graph: Bookings by Status
        # ---------------------------------------------------------------------
        statuses = ['Available', 'Booked', 'Canceled', 'Completed']
        status_counts = [Booking.query.filter_by(status=s).count() for s in statuses]

        plt.figure(figsize=(5, 4))
        plt.pie(status_counts, labels=statuses, autopct='%1.1f%%', startangle=140)
        plt.title("Booking Status Distribution")
        bookings_status_path = os.path.join(graphs_path, "bookings_status.png")
        plt.savefig(bookings_status_path)
        plt.close()

        # ---------------------------------------------------------------------
        # 3️⃣ Graph: Bookings per Theatre
        # ---------------------------------------------------------------------
        theatre_names = [t.theatre_name for t in theatres]
        theatre_counts = [Booking.query.filter_by(t_id=t.tid).count() for t in theatres]

        plt.figure(figsize=(7, 4))
        plt.barh(theatre_names, theatre_counts)
        plt.title("Total Bookings per Theatre")
        plt.xlabel("Number of Bookings")
        bookings_per_theatre_path = os.path.join(graphs_path, "bookings_per_theatre.png")
        plt.tight_layout()
        plt.savefig(bookings_per_theatre_path)
        plt.close()

        # ---------------------------------------------------------------------
        # 4️⃣ Graph: Daily Booking Trend (last 7 days)
        # ---------------------------------------------------------------------
        from datetime import timedelta
        from datetime import date
        today = date.today()
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        booking_counts = [
            Booking.query.filter(Booking.booking_date == d).count()
            for d in last_7_days
        ]

        plt.figure(figsize=(7, 4))
        plt.plot([d.strftime('%d-%b') for d in last_7_days], booking_counts, marker='o')
        plt.title("Bookings in the Last 7 Days")
        plt.xlabel("Date")
        plt.ylabel("Number of Bookings")
        daily_trend_path = os.path.join(graphs_path, "daily_trend.png")
        plt.savefig(daily_trend_path)
        plt.close()


        # ---------------------------------------------------------------------
        # Pass everything to the template
        # ---------------------------------------------------------------------
        return render_template(
            "AdminDashboard.html",
            jinjaemail=jinjaemail,
            theatres=theatres,
            users=users,
            graphs={
                "users_by_role": "graphs/users_by_role.png",
                "bookings_status": "graphs/bookings_status.png",
                "bookings_per_theatre": "graphs/bookings_per_theatre.png",
                "daily_trend": "graphs/daily_trend.png"
            }
        )

    if role == 2:
            current_user = User.query.filter_by(email=jinjaemail).first()
            uid = current_user.uid
            all_theatres=Theatre.query.all()
            from datetime import datetime,timedelta,date
            now = datetime.now()
            today = now.date()
            end_date = today + timedelta(days=7)


            # --- User's upcoming bookings (today + next 7 days, not past) ---
            all_my_bookings = (
                Booking.query.join(Theatre)
                .filter(
                    Booking.u_id == uid,
                    Booking.booking_date >= today,
                    Booking.booking_date <= end_date
                )
                .order_by(Booking.booking_date, Booking.booking_time)
                .all()
            )

            my_bookings = [
                s for s in all_my_bookings
                if datetime.combine(s.booking_date, s.booking_time) >= now
            ]

            # --- User's past bookings (before now) ---
            all_bookings_out_of_the_window = (
                Booking.query.join(Theatre)
                .filter(Booking.u_id == uid)
                .order_by(Booking.booking_date.desc(), Booking.booking_time.desc())
                .all()
            )

            past_bookings = [
                s for s in all_bookings_out_of_the_window 
                if datetime.combine(s.booking_date, s.booking_time) < now
            ]

            return render_template(
                "Dashboard.html",
                jinjaemail=jinjaemail,
                my_bookings=my_bookings,
                past_bookings=past_bookings,
                all_theatres=all_theatres
            )

    if role == 3:
        from sqlalchemy import distinct
        current_user = User.query.filter_by(email=jinjaemail).first()
        current_theatre = Theatre.query.filter_by(u_id=current_user.uid).first()
        all_theatres = Theatre.query.all()
        if not current_theatre:
            flash("No theatre found for your account.", "error")
            return redirect(url_for("dashboard_page"))
        tid = current_theatre.tid
        from datetime import timedelta,datetime
        from datetime import date
        # 2️⃣ Define time ranges 
        today = date.today()
        print(datetime.today())
        print(today)
        tomorrow = today + timedelta(days=1)
        end_date = today + timedelta(days=7)

        # 3️⃣ Today’s Appointments (booked slots today)
        todays_bookings = (
            db.session.query(Booking, User.email)
            .join(User, Booking.u_id == User.uid)
            .filter(
                Booking.t_id == tid,
                Booking.status == 'Booked',
                Booking.booking_date == today
            )
            .order_by(Booking.booking_time)
            .all()
        )

        # 4️⃣ Upcoming Bookings (booked slots for next 7 days, not including today)
        upcoming_bookings = (
            db.session.query(Booking, User.email)
            .join(User, Booking.u_id == User.uid)
            .filter(
                Booking.t_id == tid,
                Booking.status == 'Booked',
                Booking.booking_date >= tomorrow,
                Booking.booking_date <= end_date
            )
            .order_by(Booking.booking_date, Booking.booking_time)
            .all()
        )

        # 5️⃣ Find all dates that already have *any* slot (Booked or Available)
        dates_with_slots = db.session.query(distinct(Booking.booking_date)).filter(
            Booking.t_id == tid,
            Booking.booking_date >= tomorrow,
            Booking.booking_date <= end_date
        ).all()

        print(dates_with_slots)

        setup_dates = {result[0] for result in dates_with_slots}

        # 6️⃣ Build list of next 7 days and find missing ones
        next_7_days = [tomorrow + timedelta(days=i) for i in range(7)]
        missing_dates = [d for d in next_7_days if d not in setup_dates]

        # 7️⃣ Render
        return render_template(
            "TheatreDashboard.html",
            jinjaemail=jinjaemail,
            current_theatre=current_theatre,
            todays_bookings=todays_bookings,
            upcoming_bookings=upcoming_bookings,
            missing_dates=missing_dates
        )

    flash("you have not logged in")
    return redirect('/')
    
@app.route("/complete-booking", methods=["POST"])
def complete_booking():
    # --- Authentication ---
    jinjaemail = session.get("email")
    role = session.get("f_rid")
    if role != 3:  # Theatre role only
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard_page"))

    current_user = User.query.filter_by(email=jinjaemail).first()
    current_theatre = Theatre.query.filter_by(u_id=current_user.uid).first()
    if not current_theatre:
        flash("No theatre found for your account.", "error")
        return redirect(url_for("dashboard_page"))

    # --- Get booking ID from form ---
    booking_id = request.form.get("booking_id")
    if not booking_id:
        flash("No booking selected.", "error")
        return redirect('/dashboard')

    booking = Booking.query.get(booking_id)
    if not booking:
        flash("Booking not found.", "error")
        return redirect('/dashboard')

    # --- Security Check ---
    if booking.t_id != current_theatre.tid:
        flash("This booking does not belong to your theatre.", "error")
        return redirect('/dashboard')

    # --- Only allow completion for Booked slots ---
    if booking.status != "Booked":
        flash("Only booked slots can be marked as completed.", "warning")
        return redirect('/dashboard')

    # --- Get feedback from the form ---
    feedback_key = f"feedback_{booking.bid}"
    feedback_text = request.form.get(feedback_key, "").strip()

    # --- Mark booking as Completed ---
    booking.status = "Completed"
    db.session.add(booking)

    # --- Add record to CompletedBooking ---
    completed = CompletedBooking(bid=booking.bid, review=feedback_text)
    db.session.add(completed)

    db.session.commit()

    flash("Booking marked as completed successfully!", "success")
    return redirect('/dashboard')
    

@app.route("/theatre_profile/<tid>")
def theatre_profile_page(tid):
            now = datetime.now()
            today = now.date()
            end_date = today + timedelta(days=7)

     # --- Available future slots (today + next 7 days) ---
            all_available = (
                Booking.query.join(Theatre)
                .filter(
                    Booking.status == 'Available',
                    Booking.booking_date >= today,
                    Booking.booking_date <= end_date,
                    Booking.t_id == tid
                )
                .order_by(Booking.booking_date, Booking.booking_time)
                .all()
            )

            available_slots = [
                s for s in all_available
                if datetime.combine(s.booking_date, s.booking_time) > now
            ]

            return render_template(
                "theatre_profile.html",available_slots=available_slots,tid=tid)


@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.utcnow}



@app.route("/book-slot/<int:booking_id>", methods=["POST"])
def book_slot(booking_id):
    jinjaemail = session.get("email")
    role = session.get("f_rid")

    if role != 2:
        flash("You are not authorized to book slots.", "error")
        return redirect(url_for("dashboard_page"))

    current_user = User.query.filter_by(email=jinjaemail).first()
    slot = Booking.query.get(booking_id)

    if not slot:
        flash("Slot not found.", "error")
    else:
        slot_datetime = datetime.combine(slot.booking_date, slot.booking_time)
        if slot_datetime <= datetime.now():
            flash("You cannot book a past time slot.", "error")
        elif slot.status != 'Available':
            flash("Sorry, that slot has already been booked.", "warning")
        else:
            slot.status = 'Booked'
            slot.u_id = current_user.uid
            db.session.commit()
            flash("Successfully booked the slot!", "success")

    return redirect('/dashboard')


@app.route("/admin-search", methods=["GET"])
def admin_search():
    # --- Only Admins ---
    role = session.get("f_rid")
    jinjaemail = session.get("email")
    if role != 1:
        flash("Unauthorized access.", "error")
        return redirect(url_for("dashboard_page"))

    query = request.args.get("query", "").strip()
    print(query)
    if not query:
        flash("Please enter something to search.", "warning")
        return redirect(url_for("dashboard_page"))

    # --- Search Theatres ---
    theatres = Theatre.query.filter(Theatre.franchise.like(f"%{query}%")).all()

    # --- Search Users ---
    users = User.query.filter(
        (User.email.ilike(f"%{query}%")) |
        (User.uid.cast(db.String).ilike(f"%{query}%"))
    ).all()

    return render_template(
        "search_results.html",
        jinjaemail=jinjaemail,
        query=query,
        theatres=theatres,
        users=users
    )


@app.route('/logout')
def logout():
    session.pop("f_rid")
    session.pop("email")
    return redirect("/")







@app.route("/cancel-booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    jinjaemail = session.get("email")
    role = session.get("f_rid")

    if role != 2:
        flash("You are not authorized to cancel bookings.", "error")
        return redirect(url_for("dashboard_page"))

    current_user = User.query.filter_by(email=jinjaemail).first()
    slot = Booking.query.get(booking_id)

    if not slot:
        flash("Booking not found.", "error")
    elif slot.u_id != current_user.uid:
        flash("You can only cancel your own bookings.", "error")
    else:
        slot_datetime = datetime.combine(slot.booking_date, slot.booking_time)
        if slot_datetime <= datetime.now():
            flash("You cannot cancel a past or completed booking.", "warning")
        else:
            slot.status = 'Available'
            slot.u_id = None
            db.session.commit()
            flash("Your booking has been cancelled.", "success")

    return redirect('/dashboard')



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