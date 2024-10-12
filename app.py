from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from application.config import Config
from application.database import db, User, Customers, Professional, Requests, Services

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

        admin_exists = db.session.query(User).filter_by(role="Admin").first()
        if not admin_exists:
            admin = User(
                name="Akash",
                username="akashjha",
                role="Admin",
                password="123456",
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
    
    return app

app = create_app()

#----------------Signup and Login and Logut ----------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method=="POST":
        name= request.form.get("name")
        city= request.form.get("city")
        role= request.form.get("role")
        username= request.form.get("username")
        password= request.form.get("password")

        new_user = User(
                name=name,
                username=username,
                role= role,
                password= password,
                is_active= True if role=='customer' else False
            )
            
        db.session.add(new_user)
        db.session.flush() 

        if role=='customer':    
            new_customer = Customers(
                    user_id=new_user.user_id,
                    city=city
            )
            
            db.session.add(new_customer)
            
        db.session.commit()
        
        return redirect(url_for(login))
    
    return render_template('signup.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method=="POST":
        username= request.form.get("username")
        password= request.form.get("password")

        user_exists = db.session.query(User).filter_by(username=username, password=password, is_active=True).first()
    
        if not user_exists:
            flash("user does not exists",'error')
            return render_template('login.html')

        session['user_id'] = user_exists.user_id
        session['role'] = user_exists.role
        if user_exists.role =="Admin":
            return redirect(url_for('admin_home'))
        if user_exists.role =="Customer":
            return redirect(url_for('signup'))
        if user_exists.role =="Professional":
            return redirect(url_for('signup'))

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear() 
    return redirect(url_for('login')) 

#-------------------------Admin routes---------------------------------
@app.route('/admin', methods=['GET'])
def admin_home():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))
    users_count = db.session.query(Customers).count()
    professionals_count = db.session.query(Professional).count()
    completed_requests = db.session.query(Requests).filter_by(status='completed').count()
    pending_requests = db.session.query(Requests).filter_by(status='pending').count()
    not_accepted_requests = db.session.query(Requests).filter_by(proff_id=None).count()

    return render_template('admin-dashboard.html',
                         users_count=users_count,
                         professionals_count=professionals_count,
                         completed_requests=completed_requests,
                         pending_requests=pending_requests,
                         not_accepted_requests=not_accepted_requests)

@app.route('/admin-users', methods=['GET'])
def admin_users():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    customers = db.session.query(Customers).join(User).all()
    professionals = db.session.query(Professional).join(User).outerjoin(Services).all()

    return render_template('admin-users.html',
                           customers=customers,
                           professionals=professionals)

@app.route('/handle-admin-action/<int:user_id>/<string:role>', methods=['POST'])
def handle_admin_action(user_id, role):
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('admin_users'))

    if user.is_active:
        # Delete user
        if role == 'customer':
            customer = Customers.query.filter_by(user_id=user_id).first()
            if customer:
                db.session.delete(customer)
        elif role == 'professional':
            professional = Professional.query.filter_by(user_id=user_id).first()
            if professional:
                db.session.delete(professional)
        db.session.delete(user)
    else:
        # Approve user
        user.is_active = True

    db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin-add-service', methods=['GET', 'POST'])
def add_service():
    if 'user_id' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        desc = request.form.get('desc')
        min_price = request.form.get('min_price')
        min_time_req = request.form.get('min_time_req')

        new_service = Services(
            name=name,
            desc=desc,
            min_price=min_price,
            min_time_req=min_time_req
        )

        db.session.add(new_service)
        db.session.commit()

        return redirect(url_for('admin_home'))
    
    services = Services.query.all()
    return render_template('admin_add_service.html' ,services = services)

if __name__ == '__main__':
    app.run(debug=True,  port=8000)
