import os
import pymongo
from flask import (
    Flask,
    flash,
    render_template,
    redirect,
    session,
    request,
    url_for,
)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    import env


app = Flask(__name__)
app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# -----------------------------------------------------
# function to test is the mongoDB connected

# DATABASE = "task_manager"
# COLLECTION = "categories"


# def mongo_connect(url):
#     try:
#         conn = pymongo.MongoClient(url)
#         print("Mongo is connected")
#         return conn
#     except pymongo.errors.ConnectionFailure as e:
#         print("Could not connect to MongoDB: %s") % e


# conn = mongo_connect(os.environ.get("MONGO_URI"))

# coll = conn[DATABASE][COLLECTION]
# print(coll)

# documents = coll.find()
# print(documents)

# for doc in documents:
#     print(doc)
# -----------------------------------------------------


@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()}
        )

        if existing_user:
            flash("username already exists")
            return redirect(url_for("register"))
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
        }
        mongo.db.users.insert_one(register)

        # put new user in the session "cookie"
        session["user"] = request.form.get("username").lower()
        flash("registration successful")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.tasks.find({"$text":{"$search":query}}))
    return render_template("tasks.html", tasks=tasks)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()}
        )

        if existing_user:
            # check hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")
            ):
                session["user"] = request.form.get("username").lower()
                flash("welcome, {}".format(request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))
            else:
                # invalid password:
                flash("Incorrect username and/or password")
                return redirect(url_for("login"))
        else:
            # username doesnt exist
            flash("Incorrect username and/or password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # get session user's username from the database
    username = mongo.db.users.find_one({"username": session["user"]})["username"]
    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash("you have been logged out ")
    session.pop("user", None)
    return redirect(url_for("get_tasks"))


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        task = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": is_urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"],
        }
        mongo.db.tasks.insert_one(task)
        flash("Task successfully added")
        return redirect(url_for("get_tasks"))
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    if request.method == "POST":
        updated_task = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": request.form.get("is_urgent"),
            "due_date": request.form.get("due_date"),
            "created_by": session["user"],
        }
        mongo.db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": updated_task})
        flash("Task successfully updated")

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_task.html", task=task, categories=categories)


@app.route("/delete_task/<task_id>", methods=["GET", "POST"])
def delete_task(task_id):
    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})
    mongo.db.tasks.delete_one({"_id": ObjectId(task_id)})
    flash("Task successfully deleted")
    return redirect(url_for("get_tasks"))


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category = {"category_name": request.form.get("category_name")}
        mongo.db.categories.insert_one(category)
        flash("New category added successfully")
        return redirect(url_for("get_categories"))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    if request.method == "POST":
        new_category = request.form.get("category_name")
        mongo.db.categories.update_one(
            {"_id": ObjectId(category_id)}, {"$set": {"category_name": new_category}}
        )
        flash("Category updated successfully")
        return redirect(url_for("get_categories"))

    return render_template("edit_category.html", category=category)


@app.route("/delete_category/<category_id>", methods=["GET", "POST"])
def delete_category(category_id):
    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    mongo.db.categories.delete_one({"_id": ObjectId(category_id)})
    flash("Category successfully deleted")

    return redirect(url_for("get_categories"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")), debug=True)
