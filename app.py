from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from application.config import Config
from application.database import db, User, Customers, Professional, Requests, Services
import os

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

        print(role)

        new_user = User(
                name=name,
                username=username,
                role= role,
                password= password,
                is_active= True if role=='Customer' else False
            )
            
        db.session.add(new_user)
        db.session.flush() 

        if role=='Customer':    
            new_customer = Customers(
                    user_id=new_user.user_id,
                    city=city
            )
            
            db.session.add(new_customer)
        
        if role=='Professional':    
            db.session.commit()
            return redirect(url_for('professional_signup_config', user_id=new_user.user_id, city=city))
            
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method=="POST":
        username= request.form.get("username")
        password= request.form.get("password")


        print(username, password)
        user_exists = db.session.query(User).filter_by(username=username, password=password, is_active=True).first()
    
        if not user_exists:
            flash("user does not exists",'error')
            return render_template('login.html')

        session['user_id'] = user_exists.user_id
        session['role'] = user_exists.role

        
        if user_exists.role =="Admin":
            return redirect(url_for('admin_home'))
        if user_exists.role =="Customer":
            return redirect(url_for('customer_dashboard'))
        if user_exists.role =="Professional":
            return redirect(url_for('professional_dashboard'))

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
        if role == 'Customer':
            customer = Customers.query.filter_by(user_id=user_id).first()
            if customer:
                db.session.delete(customer)
        elif role == 'Professional':
            professional = Professional.query.filter_by(user_id=user_id).first()
            if professional:
                db.session.delete(professional)
        db.session.delete(user)
    else:
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

@app.route('/download/<filename>')
def download_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


#------------------customer routes---------------------------
@app.route('/customer/dashboard')
def customer_dashboard():
    if 'user_id' not in session or session['role'] != 'Customer':
        return redirect(url_for('login'))
    
    customer = Customers.query.filter_by(user_id=session['user_id']).first()
    requests = Requests.query.filter_by(cust_id=customer.cust_id).all()
    
    return render_template('customer_dashboard.html', requests=requests)

@app.route('/customer/search', methods=['GET', 'POST'])
def customer_search():
    if 'user_id' not in session or session['role'] != 'Customer':
        return redirect(url_for('login'))
    
    customer = Customers.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        search_type = request.form.get('search_type')
        
        if search_type == 'service':
            services = Services.query.filter(Services.name.ilike(f'%{search_term}%')).all()
            professionals = Professional.query.filter(
                Professional.service_id.in_([s.service_id for s in services]),
                Professional.city == customer.city
            ).all()
        else:  
            professionals = Professional.query.join(User).filter(
                User.name.ilike(f'%{search_term}%'),
                Professional.city == customer.city
            ).all()
        
        return render_template('customer_search.html', professionals=professionals, search_term=search_term)
    
    return render_template('customer_search.html')

@app.route('/customer/request_service/<int:prof_id>')
def request_service(prof_id):
    if 'user_id' not in session or session['role'] != 'Customer':
        return redirect(url_for('login'))
    
    customer = Customers.query.filter_by(user_id=session['user_id']).first()
    professional = Professional.query.get(prof_id)
    
    if not professional or professional.city != customer.city:
        flash('Invalid request or professional not available in your city.', 'error')
        return redirect(url_for('customer_search'))
    
    new_request = Requests(
        cust_id=customer.cust_id,
        service_id=professional.service_id,
        proff_id=prof_id,
        status='initiated'
    )
    db.session.add(new_request)
    db.session.commit()
    
    flash('Service request submitted successfully!', 'success')
    return redirect(url_for('customer_dashboard'))

#----------------Proffessional routes------------------
@app.route('/professional-signup-config', methods=['GET', 'POST'])
def professional_signup_config():
    user_id = request.args.get('user_id')
    city = request.args.get('city')
    if request.method=='POST':
        print("received post request")
        print(request.form.get('service_id'), user_id, city, request.form.get('experience'),  request.form.get('desc'))
        service_id = request.form.get('service_id')
        experience = request.form.get('experience')
        desc = request.form.get('desc')
        file_path=''
        file = request.files['doc']
        upload_folder = app.config['UPLOAD_FOLDER']
        
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        if file:
            filename = file.filename
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            

        docs_url = file.filename

        new_professional = Professional(
                    user_id=user_id,
                    city=city,
                    service_id=service_id,
                    experience = experience,
                    desc = desc,
                    docs_url= docs_url
            ) 
        
        db.session.add(new_professional)
        db.session.commit()

        return redirect(url_for('login'))

    user_id = request.args.get('user_id')
    city = request.args.get('city')
    services = Services.query.all()
    return render_template('professional_signup_config.html', user_id=user_id, city= city, services=services)


@app.route('/professional/dashboard')
def professional_dashboard():
    if 'user_id' not in session or session['role'] != 'Professional':
        return redirect(url_for('login'))
    
    professional = Professional.query.filter_by(user_id=session['user_id']).first()
    requests = Requests.query.filter_by(proff_id=professional.proff_id).all()
    
    return render_template('professional_dashboard.html', requests=requests)

@app.route('/professional/update_request/<int:request_id>/<string:action>')
def update_request(request_id, action):
    if 'user_id' not in session or session['role'] != 'Professional':
        return redirect(url_for('login'))
    
    request = Requests.query.get(request_id)
    if not request:
        flash('Invalid request.', 'error')
        return redirect(url_for('professional_dashboard'))
    
    if action == 'accept':
        request.status = 'ongoing'
    elif action == 'reject':
        request.status = 'rejected'
    elif action == 'complete':
        request.status = 'completed'
    else:
        flash('Invalid action.', 'error')
        return redirect(url_for('professional_dashboard'))
    
    db.session.commit()
    flash('Request updated successfully.', 'success')
    return redirect(url_for('professional_dashboard'))

@app.route('/professional/profile', methods=['GET', 'POST'])
def professional_profile():
    if 'user_id' not in session or session['role'] != 'Professional':
        return redirect(url_for('login'))
    
    professional = Professional.query.filter_by(user_id=session['user_id']).first()
    services = Services.query.all()
    
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        experience = request.form.get('experience')
        desc = request.form.get('desc')
        
        professional.service_id = service_id
        professional.experience = experience
        professional.desc = desc
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('professional_profile'))
    
    return render_template('professional_profile.html', professional=professional, services=services)
    
if __name__ == '__main__':
    app.run(debug=True,  port=8000)
