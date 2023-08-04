from sanic import Sanic
from sanic.response import json
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json as json_module

app = Sanic(__name__)

mongodb_uri = "mongodb://localhost:27017"
database_name = '20211105799'

# 创建Database类，用于处理与MongoDB的连接和操作
class Database:
    def __init__(self, uri, database_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]

    async def insert(self, collection_name, document):
        collection = self.db[collection_name]
        await collection.insert_one(document)

    def find(self, collection_name, query=None):
        collection = self.db[collection_name]
        return collection.find(query)

    async def update(self, collection_name, query, update):
        collection = self.db[collection_name]
        await collection.update_many(query, update)

    async def delete(self, collection_name, query):
        collection = self.db[collection_name]
        await collection.delete_many(query)

# 创建BookService类，用于定义与书籍相关的操作
class BookService:
    def __init__(self, database):
        self.db = database

    # 获取所有书籍信息
    async def get_all_books(self):
        books = self.db.find('books')
        return [book async for book in books]

    # 根据书籍ID获取特定书籍信息
    async def get_book(self, id):
        book = await self.db.find('books', {'_id': ObjectId(id)}).to_list(length=None)
        if book:
            return book
        else:
            return {'message': 'Book not found'}

    async def create_book(self, data):
        await self.db.insert('books', data)
        return {'message': 'Book created successfully'}

    async def update_book(self, id, data):
        query = {'_id': ObjectId(id)}
        update = {'$set': data}
        await self.db.update('books', query, update)
        return {'message': 'Book updated successfully'}

    async def delete_book(self, id):
        query = {'_id': ObjectId(id)}
        await self.db.delete('books', query)
        return {'message': 'Book deleted successfully'}

# 实例化Database对象，并传入MongoDB的URI和数据库名称
db_instance = Database(mongodb_uri, database_name)
# 使用Database对象实例化BookService对象
book_service = BookService(db_instance)

# 自定义JSONEncoder类，用于处理将MongoDB的ObjectId转换为字符串格式
class CustomJSONEncoder(json_module.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# 自定义json函数，用于将数据编码为JSON格式并返回相应
def custom_json(response_data, status=200):
    encoded_data = json_module.dumps(response_data, cls=CustomJSONEncoder)
    return json(encoded_data, status=status, content_type="application/json")

# 异常处理函数，用于处理请求过程中发生的异常
@app.exception(Exception)
async def handle_exception(request, exception):
    error_message = str(exception)
    return custom_json({'message': error_message}, status=500)


@app.route("/books", methods=["GET"])
async def get_all_books(request):
    books = await book_service.get_all_books()
    return custom_json(books)


@app.route("/book/<id>", methods=["GET"])
async def get_book(request, id):
    book = await book_service.get_book(id)
    if book:
        return custom_json(book)
    else:
        return custom_json({'message': 'Book not found'}, status=404)


@app.route("/book/create", methods=["POST"])
async def create_book(request):
    try:
        data = request.json
        result = await book_service.create_book(data)
        return custom_json(result)
    except Exception as e:
        return custom_json({'message': str(e)}, status=400)


@app.route("/book/update/<id>", methods=["PUT"])
async def update_book(request, id):
    try:
        data = request.json
        result = await book_service.update_book(id, data)
        return custom_json(result)
    except Exception as e:
        return custom_json({'message': str(e)}, status=400)


@app.route("/book/delete/<id>", methods=["DELETE"])
async def delete_book(request, id):
    try:
        result = await book_service.delete_book(id)
        return custom_json(result)
    except Exception as e:
        return custom_json({'message': str(e)}, status=400)


if __name__ == "__main__":
    app.run(port=8000)
