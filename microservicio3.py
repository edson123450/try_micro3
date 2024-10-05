from flask import Flask, request, jsonify
from pymongo import MongoClient
import logging as log
import requests

app = Flask(__name__)

# Conexión a MongoDB
client = MongoClient("mongodb://98.83.69.254:27017")
db = client["servicio_opiniones"]
reviews_collection = db["reviews"]

# Logger
log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s:\n%(message)s\n')

# DTO para manejar respuestas de microservicio2 (usuario)
class UserDTO:
    def __init__(self, name, email):
        self.name = name
        self.email = email

# DTO para manejar respuestas de microservicio1 (detalles del libro)
class BookDetailsDTO:
    def __init__(self, title, author_name):
        self.title = title
        self.author_name = author_name

@app.route('/reviews/by-book-author', methods=['GET'])
def get_reviews_by_book_and_author():
    title = request.args.get('title')
    author_name = request.args.get('authorName')

    # Llamada al microservicio 1 para obtener el book_id
    book_service_url = f"http://api-microservicio1_c:8001/books/get_book_id?title={title}&author_name={author_name}"
    book_response = requests.get(book_service_url)
    book_id = book_response.json()

    # Buscar reviews en MongoDB por book_id
    reviews = list(reviews_collection.find({"bookId": book_id}))

    # Para cada review, llamar al microservicio 2 para obtener name y email
    result = []
    for review in reviews:
        user_service_url = f"http://api-microservicio2_c:8002/users/{review['userId']}"
        user_response = requests.get(user_service_url)
        user_data = user_response.json()

        # Crear la lista con name, email, rating y comment
        review_info = [
            user_data['name'],
            user_data['email'],
            str(review['rating']),
            review['comment']
        ]
        result.append(review_info)

    return jsonify(result), 200


@app.route('/reviews/by-rating', methods=['GET'])
def get_books_by_rating():
    rating = int(request.args.get('rating'))

    # Buscar reviews en MongoDB por rating
    reviews = list(reviews_collection.find({"rating": rating}))

    # Llamada al microservicio 1 para obtener el título y nombre del autor por cada book_id
    result = []
    for review in reviews:
        book_service_url = f"http://api-microservicio1_c:8001/books/{review['bookId']}/details"
        book_response = requests.get(book_service_url)
        book_data = book_response.json()

        # Crear la lista con title y author_name
        book_info = [
            book_data['title'],
            book_data['authorName']
        ]
        result.append(book_info)

    return jsonify(result), 200


@app.route('/reviews/new', methods=['POST'])
def add_new_review():
    review_data = request.get_json()

    # Guardar nueva review en MongoDB
    new_review = {
        "bookId": review_data.get("bookId"),
        "authorId": review_data.get("authorId"),
        "userId": review_data.get("userId"),
        "rating": review_data.get("rating"),
        "comment": review_data.get("comment")
    }

    reviews_collection.insert_one(new_review)
    return jsonify({"message": "Review saved successfully"}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)
