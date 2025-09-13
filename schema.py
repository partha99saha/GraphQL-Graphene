import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from models import User
from database import SessionLocal
from auth import hash_password, verify_password
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    decode_token,
)
from graphql import GraphQLError

db = SessionLocal()


# GraphQL type for User
class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User


class Query(graphene.ObjectType):
    users = graphene.List(UserType)

    def resolve_users(root, info):
        # Get Authorization header
        auth = info.context.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise GraphQLError("Missing or invalid Authorization header")

        # Extract token
        token = auth.split(" ")[1]

        # Decode token
        try:
            decoded = decode_token(token)
            user_id = decoded["sub"]  # this is your user ID as string
        except Exception as e:
            raise GraphQLError(f"Invalid token: {str(e)}")

        # Optional: check if user exists in DB
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise GraphQLError("User not found")

        # Return all users
        return db.query(User).all()


# Mutations
class Register(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(lambda: UserType)

    def mutate(root, info, username, password):
        hashed = hash_password(password)
        user = User(username=username, password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        return Register(ok=True, user=user)


class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()

    def mutate(root, info, username, password):
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password):
            # Identity must be a string
            token = create_access_token(identity=str(user.id))
            # print("token", token)
            return Login(token=token)
        return Login(token=None)


class Mutation(graphene.ObjectType):
    register = Register.Field()
    login = Login.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
