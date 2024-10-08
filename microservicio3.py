from flask import Flask, request, jsonify, Response, json
from pymongo import MongoClient
import logging as log
import requests
from bson import ObjectId

app = Flask(__name__)

# Clase MongoAPI para manejar la conexión y las operaciones sobre MongoDB
class MongoAPI:
    def __init__(self, data):
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s:\n%(message)s\n')
        self.client = MongoClient("mongodb://98.83.69.254:8007")  # Conexión MongoDB
        database = data['database']
        collection = data['collection']
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data

    def find_reviews_by_book_id(self, book_id):
        log.info('Buscando reviews por book_id')
        reviews = list(self.collection.find({"book_id": book_id}))
        for review in reviews:
            review['_id'] = str(review['_id'])  # Convertir ObjectId a string
        return reviews

    def find_reviews_by_rating(self, rating):
        log.info('Buscando reviews por rating')
        reviews = list(self.collection.find({"rating": rating}))
        for review in reviews:
            review['_id'] = str(review['_id'])  # Convertir ObjectId a string
        return reviews

    def find_all_reviews(self):
        log.info('Buscando todos los reviews')
        reviews = list(self.collection.find())
        for review in reviews:
            review['_id'] = str(review['_id'])  # Convertir ObjectId a string
        return reviews

    def insert_review(self, review_data):
        log.info('Guardando una nueva review')
        response = self.collection.insert_one(review_data)
        output = {'Status': 'Successfully Inserted', 'Document_ID': str(response.inserted_id)}
        return output

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

@app.route('/')
def base():
    return Response(response=json.dumps({"Status": "UP"}),
                    status=200,
                    mimetype='application/json')

# Ruta para obtener reviews por título y autor
@app.route('/reviews/by-book-author', methods=['GET'])
def get_reviews_by_book_and_author():
    data = request.json
    title = request.args.get('title')
    author_name = request.args.get('authorName')

    # Llamada al microservicio 1 para obtener el book_id
    book_service_url = f"http://api-microservicio1_c:8001/books/get_book_id?title={title}&author_name={author_name}"
    book_response = requests.get(book_service_url)
    book_id = book_response.json().get('book_id')

    if not book_id:
        return jsonify({"error": "Book not found"}), 404

    # Crear instancia de MongoAPI para operar en la base de datos y colección proporcionadas
    mongo_api = MongoAPI(data)

    # Buscar reviews en MongoDB por book_id
    reviews = mongo_api.find_reviews_by_book_id(book_id)

    # Para cada review, llamar al microservicio 2 para obtener name y email
    result = []
    for review in reviews:
        user_service_url = f"http://api-microservicio2_c:8002/users/{review['user_id']}"
        user_response = requests.get(user_service_url)
        user_data = user_response.json()

        # Crear la lista con name, email, rating y comment
        review_info = [
            user_data.get('name', 'Unknown'),
            user_data.get('email', 'Unknown'),
            str(review['rating']),
            review['comment']
        ]
        result.append(review_info)

    return jsonify(result), 200

# Ruta para obtener libros por rating
@app.route('/reviews/by-rating', methods=['GET'])
def get_books_by_rating():
    data = request.json
    rating = int(request.args.get('rating'))

    # Crear instancia de MongoAPI para operar en la base de datos y colección proporcionadas
    mongo_api = MongoAPI(data)

    # Buscar reviews en MongoDB por rating
    reviews = mongo_api.find_reviews_by_rating(rating)

    # Llamada al microservicio 1 para obtener el título y nombre del autor por cada book_id
    result = []
    for review in reviews:
        book_service_url = f"http://api-microservicio1_c:8001/books/{review['book_id']}/details"
        book_response = requests.get(book_service_url)
        book_data = book_response.json()

        if book_data.get('title') and book_data.get('author_name'):
            # Crear la lista con title y author_name
            book_info = [
                book_data['title'],
                book_data['author_name']
            ]
            result.append(book_info)
        else:
            result.append({"error": "Book or author details not found"})

    return jsonify(result), 200

# Ruta para obtener todos los reviews
@app.route('/reviews/all', methods=['GET'])
def get_all_reviews():
    data = request.json

    # Crear instancia de MongoAPI para operar en la base de datos y colección proporcionadas
    mongo_api = MongoAPI(data)

    # Buscar todos los reviews en MongoDB
    reviews = mongo_api.find_all_reviews()

    # Convertir los resultados en JSON y devolverlos
    return jsonify(reviews), 200

# Ruta para guardar una nueva review
@app.route('/reviews/new', methods=['POST'])
def add_new_review():
    data = request.json

    # Crear instancia de MongoAPI para operar en la base de datos y colección proporcionadas
    mongo_api = MongoAPI(data)

    # Extraer y guardar la nueva review en MongoDB
    new_review = {
        "book_id": data.get("book_id"),
        "author_id": data.get("author_id"),
        "user_id": data.get("user_id"),
        "rating": data.get("rating"),
        "comment": data.get("comment")
    }

    response = mongo_api.insert_review(new_review)
    return jsonify(response), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003, debug=True)
