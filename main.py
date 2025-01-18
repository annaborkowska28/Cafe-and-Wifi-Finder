from flask import Flask,render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
from dotenv import load_dotenv



app = Flask(__name__)
bootstrap = Bootstrap5(app)
# CREATE DB
class Base(DeclarativeBase):
    pass
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SECRET_KEY'] = os.getenv('secret_key')
db = SQLAlchemy(model_class=Base)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



# CREATE TABLE

class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        """function that converts an object's attributes into a dictionary. It uses a dictionary comprehension to
         iterate over the columns of the object's table and creates key-value pairs where the key is
          the column name and the value is the corresponding attribute value of the object"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# with app.app_context():
#     db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":

        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))

        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            password=hash_and_salted_password,
            username=request.form.get('username')
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Registration successful! Welcome!')
        return redirect(url_for("home"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash(f'Login successful! Welcome back!')
            return redirect(url_for('home'))
    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # This will clear all session data
    flash('You have been logged out. See you again soon!')
    return redirect(url_for('home'))



#--------------------- HOME PAGE WITH ALL CAFES ------------
@app.route("/")
def home():
#retrieve all café records from the database, ordered by their ID,
    all_cafes = Cafe.query.order_by(Cafe.id).all()
# iterates through the all_cafes list, assigning a ranking to each café based on its position in the list.
#The ranking is calculated as the total number of cafés minus the current index (i),
# ranking them in descending order (with the highest rank being 1 for the first café).
    for i in range(len(all_cafes)):
        all_cafes[i].ranking = len(all_cafes) - i
    db.session.commit()
#
    counter = 0
    cafes_to_append = []
    second_list = []
#     # 2 list: first for temporarily holding cafés and 2nd for storing groups of three cafés.
    for _ in all_cafes:
        cafes_to_append.append(all_cafes[counter])
        counter += 1
        if len(cafes_to_append) % 3 != 0:
            continue
        else:
            second_list.append(cafes_to_append)
            cafes_to_append = []
   # if there are any remaining café it appends this leftover list to second list
    if len(cafes_to_append) > 0:
        second_list.append(cafes_to_append)
    return render_template("index.html", all_cafes=second_list)





#------------------------- ADD NEW CAFE ----------------------------------------
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_cafe():
    if request.method == 'POST':
        new_cafe = Cafe(
            name=request.form['name'],
            map_url=request.form['map_url'],
            img_url=request.form['img_url'],
            location=request.form['location'],
            has_sockets=int(request.form['has_sockets']),
            has_toilet=int(request.form['has_toilet']),
            has_wifi=int(request.form['has_wifi']),
            can_take_calls=int(request.form['can_take_calls']),
            seats=request.form['seats'],
            coffee_price=request.form['coffee_price'])
        db.session.add(new_cafe)
        db.session.commit()
        db.session.close_all()
        return redirect(url_for("home"))
    return render_template("add.html")


@app.route('/edit', methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        try:
            cafe_id = request.form['id']
            cafe_to_update = db.get_or_404(Cafe, cafe_id)
            # Debug print to check form data received
            # print("Form Data:", request.form)
            cafe_to_update.name = request.form['name']
            cafe_to_update.map_url = request.form['map_url']
            cafe_to_update.img_url = request.form['img_url']
            cafe_to_update.location = request.form['location']
            cafe_to_update.has_sockets = int(request.form['has_sockets'])
            cafe_to_update.has_toilet = int(request.form['has_toilet'])
            cafe_to_update.has_wifi = int(request.form['has_wifi'])
            cafe_to_update.can_take_calls = int(request.form['can_take_calls'])
            cafe_to_update.seats = request.form['seats']
            cafe_to_update.coffee_price = request.form['coffee_price']
            db.session.commit()
            return redirect(url_for('home'))
        except KeyError as e:
            flash(f"Missing form field: {e}")
            return redirect(url_for('edit', id=request.form['id']))
    cafe_id = request.args.get('id')
    cafe_selected = db.get_or_404(Cafe, cafe_id)

    return render_template('edit.html', cafe=cafe_selected)


@app.route('/delete')
@login_required
def delete():
    cafe_id = request.args.get('id')
    cafe_to_delete = db.get_or_404(Cafe, cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/search')
def search():
    location = request.args.get('location').lower()
    if location:
        cafes = Cafe.query.filter(Cafe.location.ilike(f'{location}')).all()
    else:
        cafes = []

    return render_template('search.html', cafes=cafes, location=location)

if __name__ == '__main__':
    app.run(debug=True)



