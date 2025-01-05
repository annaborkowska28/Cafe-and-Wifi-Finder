from flask import Flask,render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from flask_bootstrap import Bootstrap5
import os
from dotenv import load_dotenv
'''
Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

'''

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


# CREATE TABLE
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
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# with app.app_context():
#     db.create_all()



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
def add_cafe():
    if request.method == 'POST':
        cafe_name = request.form['name']
        map_url = request.form['map_url']
        img_url = request.form['img_url']
        location = request.form['location']
        has_sockets = int(request.form['has_sockets'])
        has_toilet = int(request.form['has_toilet'])
        has_wifi = int(request.form['has_wifi'])
        can_take_calls = int(request.form['can_take_calls'])
        seats = request.form['seats']
        coffee_price = request.form['coffee_price']
        new_cafe = Cafe(name=cafe_name,
                        map_url=map_url,
                        img_url=img_url,
                        location=location,
                        has_sockets=has_sockets,
                        has_toilet=has_toilet,
                        has_wifi=has_wifi,
                        can_take_calls=can_take_calls,
                        seats=seats,
                        coffee_price=coffee_price)
        db.session.add(new_cafe)
        db.session.commit()
        db.session.close_all()
        return redirect(url_for("home"))
    return render_template("add.html")


if __name__ == '__main__':
    app.run(debug=True)
