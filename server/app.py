#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

EXEMPT_ROUTES = ['/signup', '/login', '/check_session']

@app.before_request
def require_login():
    if request.path in EXEMPT_ROUTES or request.method == 'OPTIONS':
        return
    if not session.get('user_id'):
        return {"error": "Unauthorized"}, 401

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            new_user = User(
                username=data.get("username"),
                image_url=data.get("image_url"),
                bio=data.get("bio")
            )
            new_user.password_hash = data.get("password")
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id

            return new_user.to_dict(), 201

        except IntegrityError:
            db.session.rollback()
            return {'errors': 'Username must be unique'}, 422

        except Exception as e:
            return {'errors': str(e)}, 422


class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User,user_id)
            return user.to_dict(), 200
        return {"error": "Unauthorized"}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get("username")).first()

        if user and user.authenticate(data.get("password")):
            session["user_id"] = user.id
            return user.to_dict(), 200
        return {"error": "Invalid username or password"}, 401

class Logout(Resource):
    def delete(self):
        session.pop("user_id", None)
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        data = request.get_json()

        try:
            new_recipe = Recipe(
                title=data.get("title"),
                instructions=data.get("instructions"),
                minutes_to_complete=data.get("minutes_to_complete"),
                user_id=session.get("user_id")
            )
            db.session.add(new_recipe)
            db.session.commit()

            return new_recipe.to_dict(), 201

        except IntegrityError:
            db.session.rollback()
            return {"errors": "Invalid data or duplicate entry"}, 422

        except Exception as e:
            return {"errors": str(e)}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)