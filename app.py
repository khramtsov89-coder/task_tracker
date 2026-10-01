from flask import Flask, request, jsonify
import models

app = Flask(__name__)
models.init_db()


@app.route("/tasks", methods=["GET"])
def list_tasks():
    return jsonify(models.get_all_tasks())


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    task = models.create_task(title)
    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = models.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    task = models.update_task(task_id, title=data.get("title"), done=data.get("done"))
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


# QA завёл баг по этому эндпоинту, см. тикет в чате
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = models.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    models.delete_task(task_id)
    return jsonify({"message": "Task deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True)
