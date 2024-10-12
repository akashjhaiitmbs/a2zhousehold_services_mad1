from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from application.config import Config
from application.database import db, User, Customers, Professional, Requests

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
        
        print(new_customer)
        print(new_user)
        return redirect(url_for(login))
    
    return render_template('signup.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method=="POST":
        username= request.form.get("username")
        password= request.form.get("password")

        user_exists = db.session.query(User).filter_by(username=username, password=password, is_active=True).first()
    
        if not user_exists:
            return redirect(url_for(signup))

        session['user_id'] = user_exists.user_id
        session['role'] = user_exists.role
        if user_exists.role =="Admin":
            return redirect(url_for('admin_home'))
        if user_exists.role =="Customer":
            return redirect(url_for(signup))
        if user_exists.role =="Professional":
            return redirect(url_for(signup))

        return redirect(url_for(signup))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear() 
    return redirect(url_for('login')) 

#-------------------------Admin routes---------------------------------
@app.route('/admin', methods=['GET'])
def admin_home():
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
    users = User.query.all()
    return render_template('admin-users.html',
                         users =users)


@app.route('/handle_admin_action/<int:user_id>', methods=['POST'])
def handle_admin_action(user_id):
    user = User.query.filter(user_id=user_id)

    if user.is_active:
        db.session.delete(user)
    else:
        user.is_active= True
    db.session.commit()

    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    app.run(debug=True,  port=8000)
