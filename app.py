from bson.objectid import ObjectId
from flask import Flask, redirect, render_template, request, url_for
import os
from pymongo import MongoClient

# Flask simple setup
app = Flask(__name__)
# app.config["ENV"] = "development"

host = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/Songs')
client = MongoClient(host=f'{host}?retryWrites=false')    #MongoClient()
# client = MongoClient()
#songs_db = client.Songs
songs_db = client.get_default_database()

songs_collection = songs_db.songs
cart_collection = songs_db.cart

description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus vitae ultrices enim. Vestibulum semper arcu ac turpis tincidunt sagittis. Maecenas et auctor sapien, id lobortis erat. Ut sit amet elementum lectus. Cras in urna vel enim lacinia sagittis. Vivamus id tincidunt diam, nec scelerisque lacus."

songs_collection.delete_many({})
cart_collection.delete_many({})
songs_collection.insert_one({
    "title": "Birds of a feather flock together",
    "artist": "Jack Sparrow",
    "price": 800,
    "description": description,
})
songs_collection.insert_one({
    "title": "Go Fish",
    "artist": "Fisherman",
    "price": 19000,
    "description": description,
})
cart_collection.insert_one({
    "_id": "properties",
    "total_count": 0,
    "total_cost": 0.0,
})


def cart_count():
    return cart_collection.find_one({"_id": "properties"})["total_count"]


def change_item_count_for_cart(item_id, target_quantity):
    item = cart_collection.find_one({"_id": ObjectId(item_id)})
    song_for_item = songs_collection.find_one({"_id": ObjectId(item_id)})
    cart_properties = cart_collection.find_one({"_id": "properties"})
    item_price = song_for_item["price"]
    new_item_cost = target_quantity * item_price
    delta_item_count = target_quantity - item["count"]
    delta_item_cost = delta_item_count * item_price
    print("old properties: ")
    print(cart_collection.find_one({"_id":"properties"}))
    print(item)
    cart_collection.update_one({"_id": "properties"}, {
        "$inc": {
            "total_cost": item_price * (target_quantity - item["count"]),
            "total_count": target_quantity - item["count"]
        }
    })
    print("new properties: ")
    print(cart_collection.find_one({"_id":"properties"}))
    if not target_quantity:
        # target_quantity is being set to 0, so delete the item from cart_collection
        cart_collection.delete_one({"_id": ObjectId(item_id)})
    else:
        cart_collection.update_one({"_id": ObjectId(item_id)}, {
            "$set": {
                "cost": new_item_cost,
                "count": target_quantity
            }
        })

    print(cart_collection.find_one({"_id": ObjectId(item_id)}))


@app.route("/songs")
@app.route("/")
def songs_view():
    """Show all songs."""
    return render_template("songs_view.html",
                           songs=songs_collection.find(),
                           cart_size=cart_count())


@app.route("/songs/<song_id>")
def songs_detail(song_id):
    """Show details for a song"""
    song = songs_collection.find_one({"_id": ObjectId(song_id)})
    return render_template("songs_detail.html",
                           song=song,
                           cart_size=cart_count())


@app.route("/songs/add_to_cart/<song_id>")
def songs_add_to_cart(song_id):
    song_in_cart = cart_collection.find_one({"_id": ObjectId(song_id)})
    song = songs_collection.find_one({"_id": ObjectId(song_id)})

    if not song_in_cart:
        # song wasn't found in cart
        cart_collection.insert_one({
            "_id": ObjectId(song_id),
            "count": 0,
            "cost": 0.0,
            "title": song["title"],
        })
    cart_collection.update_one({"_id": ObjectId(song_id)},
                               {"$inc": {
                                   "count": 1,
                                   "cost": song["price"]
                               }})
    cart_collection.update_one(
        {"_id": "properties"},
        {"$inc": {
            "total_count": 1,
            "total_cost": song["price"],
        }})

    return redirect(url_for("songs_view"))


@app.route("/songs/cart")
def cart_view():
    return render_template("cart_view.html",
                           title="my cart",
                           cart=cart_collection.find(),
                           cart_size=cart_count(),
                           cart_total=cart_collection.find_one(
                               {"_id": "properties"})["total_cost"])


@app.route("/songs/cart/update_quantity/<cart_item_id>", methods=["POST"])
def cart_update_quantity(cart_item_id):
    change_item_count_for_cart(cart_item_id, int(request.form.get("quantity")))
    return redirect(url_for("cart_view"))


@app.route("/songs/cart/delete_item/<cart_item_id>", methods=["POST"])
def cart_delete_item(cart_item_id):
    change_item_count_for_cart(cart_item_id, 0)
    return redirect(url_for("cart_view"))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
