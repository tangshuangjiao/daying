import jsonschema
from sanic import Sanic
from sanic.response import json as custom_json
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from jsonschema import validate

app = Sanic(__name__)

# 创建MongoDB连接
client = AsyncIOMotorClient("mongodb://localhost:27017")
db_instance = client["20211105799"]


class BaseService:
    def __init__(self, collection_name):
        self.collection_name = collection_name

    @property
    def collection(self):
        return db_instance[self.collection_name]

    async def find(self, query, projection=None):
        try:
            return await self.collection.find(query, projection=projection).to_list(length=None)
        except Exception as e:
            return []

    async def insert(self, data):
        try:
            return await self.collection.insert_one(data)
        except Exception as e:
            return None

    async def update(self, query, data):
        try:
            return await self.collection.update_one(query, {'$set': data})
        except Exception as e:
            return None

    async def delete(self, query):
        try:
            return await self.collection.delete_one(query)
        except Exception as e:
            return None

class UserService(BaseService):
    def get_user_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "username": {"type": "string", "uniqueItems": True},
                "employee_id": {"type": "string"},
                "phone": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "hire_date": {"type": "string", "format": "date"},
                "position": {"type": "string"},
                "department": {
                    "type": "object",
                    "properties": {
                        "_id": {"type": "string"},
                        "name": {"type": "string"}
                    },
                    "required": ["_id", "name"]
                },
                "permissions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "_id": {"type": "string"},
                            "name": {"type": "string"}
                        },
                        "required": ["_id", "name"]
                    }
                }
            },
            "required": ["name", "username", "employee_id", "phone", "email", "hire_date", "position", "department",
                         "permissions"]
        }

        return schema

    async def insert(self, data):
        # 验证用户数据的有效性
        schema = self.get_user_schema()
        try:
            validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            return {'message': str(e)}
        return await self.collection.insert_one(data)

    async def get_users(self):
        projection = {
            "name": 1,
            "employee_id": 1,
            "position": 1,
            "department.name": 1
        }
        users = await self.find({}, projection=projection)
        return users

    async def get_user_info(self, id):
        query = {'_id': ObjectId(id)}
        projection = {
            'name': 1,
            'username': 1,
            'employee_id': 1,
            'phone': 1,
            'email': 1,
            'hire_date': 1,
            'position': 1,
            'department': 1,
            'permissions': 1
        }
        user = await self.find(query, projection=projection)

        if user:
            return user[0]
        else:
            return {'message': 'User not found'}

    async def update_user_profile(self, id, data):
        try:
            # 检查是否有权限和部门更新
            if "department" in data or "permissions" in data:
                user = await self.collection.find_one({"_id": ObjectId(id)})
                if user is None:
                    return {'message': 'User not found'}

                if "department" in data:
                    department_id = data["department"]["_id"]
                    department_name = data["department"]["name"]
                    # 更新用户的部门信息
                    await self.update({'_id': ObjectId(id)},
                                      {"department": {"_id": department_id, "name": department_name}})

                if "permissions" in data:
                    permissions = data["permissions"]
                    # 更新用户的权限信息
                    await self.update({'_id': ObjectId(id)}, {"permissions": permissions})

            result = await self.update({'_id': ObjectId(id)}, {'$set': data})
            if result.modified_count > 0:
                return {'message': 'User profile updated successfully'}
            else:
                return {'message': 'User not found'}
        except Exception as e:
            print(f"Failed to update user profile: {e}")
            return {'message': 'Error occurred while updating user profile'}

    async def delete_user(self, id):
        result = await self.delete({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return {'message': 'User deleted successfully'}
        else:
            return {'message': 'User not found'}

class PermissionService(BaseService):
    def get_permission_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "permissions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["name", "permissions"]
        }

        return schema

    async def insert(self, data):
        # 验证权限数据的有效性
        schema = self.get_permission_schema()
        try:
            validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            return {'message': str(e)}
        return await self.collection.insert_one(data)

    async def update(self, id, data):
        result = await self.collection.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.modified_count > 0:
            return {'message': 'Permission group updated successfully'}
        else:
            return {'message': 'Permission group not found'}

    async def delete(self, id):
        result = await self.collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return {'message': 'Permission group deleted successfully'}
        else:
            return {'message': 'Permission group not found'}

class DepartmentService(BaseService):
    def get_department_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "parent": {"type": "string", "default": ""}
            },
            "required": ["name"]
        }

        return schema

    async def insert(self, data):
        # 验证部门数据的有效性
        schema = self.get_department_schema()
        try:
            validate(data, schema)
        except jsonschema.exceptions.ValidationError as e:
            return {'message': str(e)}
        return await self.collection.insert_one(data)

    async def update(self, id, data):
        result = await self.collection.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.modified_count > 0:
            return {'message': 'Department updated successfully'}
        else:
            return {'message': 'Department not found'}

    async def delete(self, id):
        result = await self.collection.delete_one({'_id': ObjectId(id)})
        if result.deleted_count > 0:
            return {'message': 'Department deleted successfully'}
        else:
            return {'message': 'Department not found'}


user_service = UserService('users')
permission_service = PermissionService('permissions')
department_service = DepartmentService('departments')

@app.route("/user", methods=["GET"])
async def get_users(request):
    users = await user_service.get_users()
    return custom_json(users)


@app.route("/user/<id>", methods=["GET"])
async def get_user(request, id):
    user = await user_service.get_user_info(id)
    if user:
        return custom_json(user)
    else:
        return custom_json({'message': 'User not found'}, status=404)


@app.route("/user/update/<id>", methods=["PUT"])
async def update_user(request, id):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)

    # 更新用户资料
    user_result = await user_service.update_user_profile(id, data)

    # 更新权限组
    permission_data = data.get("permissions")
    if permission_data:
        permission_result = await permission_service.update(id, permission_data)

    # 更新部门信息
    department_data = data.get("department")
    if department_data:
        department_result = await department_service.update(id, department_data)

    return custom_json({"user": user_result, "permission": permission_result, "department": department_result})


@app.route("/user/delete/<id>", methods=["DELETE"])
async def delete_user(request, id):
    result = await user_service.delete_user(id)
    return custom_json(result)


@app.route("/permission", methods=["POST"])
async def create_permission(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await permission_service.insert(data)
    return custom_json(result)


@app.route("/permission/update/<id>", methods=["PUT"])
async def update_permission(request, id):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await permission_service.update(id, data)
    return custom_json(result)


@app.route("/permission/delete/<id>", methods=["DELETE"])
async def delete_permission(request, id):
    result = await permission_service.delete(id)
    return custom_json(result)


@app.route("/department", methods=["POST"])
async def create_department(request):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await department_service.insert(data)
    return custom_json(result)


@app.route("/department/update/<id>", methods=["PUT"])
async def update_department(request, id):
    data = request.json
    if data is None:
        return custom_json({'message': 'Invalid request data'}, status=400)
    result = await department_service.update(id, data)
    return custom_json(result)


@app.route("/department/delete/<id>", methods=["DELETE"])
async def delete_department(request, id):
    result = await department_service.delete(id)
    return custom_json(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
