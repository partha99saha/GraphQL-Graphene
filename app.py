from flask import Flask, request, jsonify
from schema import schema
from auth import init_jwt
from database import Base, engine

app = Flask(__name__)
init_jwt(app)

# Create tables if they don’t exist
Base.metadata.create_all(bind=engine)


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    result = schema.execute(
        data.get("query"),
        context_value=request,  # pass request to resolvers for JWT
        variable_values=data.get("variables"),
    )

    response = {}
    if result.errors:
        response["errors"] = [str(err) for err in result.errors]
    if result.data:
        response["data"] = result.data

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
