from sanic import Sanic
from sanic.response import json
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json as json_module

app = Sanic(__name__)

mongodb_uri = "mongodb://localhost:27017"
database_name = 'usermanagement'

class Database:
    def __init__(self, uri, database_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]

    async def insert(self, collection_name, document):
        # 向指定集合插入一条文档
        collection = self.db[collection_name]
        try:
            await collection.insert_one(document)
        except Exception as e:
            print(f"Error occurred while inserting document: {e}")

    def find(self, collection_name, query=None):
        # 在指定集合中查询符合条件的文档
        collection = self.db[collection_name]
        try:
            return collection.find(query)
        except Exception as e:
            print(f"Error occurred while finding documents: {e}")
            return None

    async def update(self, collection_name, query, update):
        # 更新指定集合中符合条件的文档
        collection = self.db[collection_name]
        try:
            await collection.update_many(query, update)
        except Exception as e:
            print(f"Error occurred while updating documents: {e}")

    async def delete(self, collection_name, query):
        # 删除指定集合中符合条件的文档
        collection = self.db[collection_name]
        try:
            await collection.delete_many(query)
        except Exception as e:
            print(f"Error occurred while deleting documents: {e}")


class BaseService:
    def __init__(self, database, collection_name):
        self.db = database
        self.collection_name = collection_name

    async def get_all_items(self):
        # 获取所有信息
        data = self.db.find(self.collection_name)
        return [item async for item in data]

    async def find_by_id(self, id):
        # 根据ID获取信息
        query = {'_id': ObjectId(id)}
        item = await self.db.find(self.collection_name, query).to_list(length=None)
        if item:
            return item
        else:
            return {'message': 'Item not found'}

    async def create_item(self, data):
        # 创建信息
        try:
            await self.db.insert(self.collection_name, data)
            return {'message': 'Item created successfully'}
        except Exception as e:
            # 处理异常
            print(f"创建信息时出现异常: {e}")
            return {'message': 'Error occurred while creating item'}

    async def update_item(self, id, data):
        # 更新信息
        try:
            await self.db.update(self.collection_name, {'_id': ObjectId(id)}, {'$set': data})
            return {'message': 'Item updated successfully'}
        except Exception as e:
            # 处理异常
            print(f"更新信息时出现异常: {e}")
            return {'message': 'Error occurred while updating item'}

    async def delete_item(self, id):
        # 删除信息
        try:
            await self.db.delete(self.collection_name, {'_id': ObjectId(id)})
            return {'message': 'Item deleted successfully'}
        except Exception as e:
            # 处理异常
            print(f"删除信息时出现异常: {e}")
            return {'message': 'Error occurred while deleting item'}



# 创建数据库实例
db_instance = Database(mongodb_uri, database_name)
# 创建用户、权限和部门操作服务实例
user_service = BaseService(db_instance, 'users')
permission_service = BaseService(db_instance, 'permissions')
department_service = BaseService(db_instance, 'departments')


# 自定义JSON编码器，用于处理ObjectId类型的数据
class CustomJSONEncoder(json_module.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

 #将response_data 转换为 JSON 格式，并返回一个 JSON 响应对象
def custom_json(response_data, status=200):
    encoded_data = json_module.dumps(response_data, cls=CustomJSONEncoder)
    return json(encoded_data, status=status, content_type="application/json")

@app.exception(Exception)
async def handle_exception(request, exception):
    error_message = str(exception)
    return custom_json({'message': error_message}, status=500)


# 用户相关路由
@app.route("/users", methods=["GET"])
async def get_all_users(request):
    users = await user_service.get_all_items()
    return custom_json(users)

@app.route("/user/<id>", methods=["GET"])
async def get_user(request,id):
    user = await user_service.find_by_id(id)
    if user:
        return custom_json(user)
    else:
        return custom_json({'message': 'User not found'}, status=404)

@app.route("/user/create", methods=["POST"])
async def create_user(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await user_service.create_item(data)
    if result is None:
        return custom_json({'message': 'Failed to create user'}, status=500)
    return custom_json(result)

@app.route("/user/update/<id>", methods=["PUT"])
async def update_user(request, id):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await user_service.update_item(id, data)
    if result is None:
        return custom_json({'message': 'Failed to update user'}, status=500)
    return custom_json(result)

@app.route("/user/delete/<id>", methods=["DELETE"])
async def delete_user(request,id):
    result = await user_service.delete_item(id)
    if result is None:
        return custom_json({'message': 'Failed to delete user'}, status=500)
    return custom_json(result)



# 权限相关路由
@app.route("/permissions", methods=["GET"])
async def get_all_permissions(request):
    permissions = await permission_service.get_all_items()
    return custom_json(permissions)

@app.route("/permission/<id>", methods=["GET"])
async def get_permission(request,id):
    permission = await permission_service.find_by_id(id)
    if permission:
        return custom_json(permission)
    else:
        return custom_json({'message': 'Permission not found'}, status=404)

@app.route("/permission/create", methods=["POST"])
async def create_permission(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await permission_service.create_item(data)
    if result is None:
        return custom_json({'message': 'Failed to create permission'}, status=500)
    return custom_json(result)

@app.route("/permission/update/<id>", methods=["PUT"])
async def update_permission(request, id):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await permission_service.update_item(id, data)
    if result is None:
        return custom_json({'message': 'Failed to update permission'}, status=500)
    return custom_json(result)

@app.route("/permission/delete/<id>", methods=["DELETE"])
async def delete_permission(request,id):
    if id is None:
        return custom_json({'message': 'Invalid permission ID'}, status=400)
    result = await permission_service.delete_item(id)
    if result is None:
        return custom_json({'message': 'Failed to delete permission'}, status=500)
    return custom_json(result)



# 部门相关路由
@app.route("/departments", methods=["GET"])
async def get_all_departments(request):
    departments = await department_service.get_all_items()
    return custom_json(departments)

@app.route("/department/<id>", methods=["GET"])
async def get_department(request,id):
    department = await department_service.find_by_id(id)
    if department:
        return custom_json(department)
    else:
        return custom_json({'message': 'Department not found'}, status=404)

@app.route("/department/create", methods=["POST"])
async def create_department(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await department_service.create_item(data)
    if result is None:
        return custom_json({'message': 'Failed to create department'}, status=500)
    return custom_json(result)

@app.route("/department/update/<id>", methods=["PUT"])
async def update_department(request, id):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await department_service.update_item(id, data)
    if result is None:
        return custom_json({'message': 'Failed to update department'}, status=500)
    return custom_json(result)

@app.route("/department/delete/<id>", methods=["DELETE"])
async def delete_department(request,id):
    if id is None:
        return custom_json({'message': 'Invalid request'}, status=400)
    result = await department_service.delete_item(id)
    if result is None:
        return custom_json({'message': 'Failed to delete department'}, status=500)
    return custom_json(result)


if __name__ == "__main__":
    app.run(port=8000)
