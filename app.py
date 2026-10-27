from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import models
load_dotenv()

app = Flask(__name__)
models.init_db()


@app.route("/tasks", methods=["GET"])
def list_tasks():
    done_status = request.args.get("done")
    sort = request.args.get("sort")
    all_tasks = models.get_all_tasks()
    
    if done_status is not None:
        done_status = done_status.lower()
        if done_status == "true":
            tasks = [task for task in all_tasks if task.get("done") is True]
        elif done_status == "false":
            tasks = [task for task in all_tasks if task.get("done") is False]
        else:
            tasks = all_tasks
    else:
        tasks = all_tasks
    if sort == "created_at":
        tasks = sorted(tasks, key=lambda t: t["created_at"])
    elif sort == "-created_at":
        tasks = sorted(tasks, key=lambda t: t["created_at"], reverse=True)
    return jsonify(tasks)



@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if title is None or title.strip() == "":
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 100:
        return jsonify({"error": "Title is too long"}), 400
    title = title.strip()
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
    done_status = data.get("done")
    if "done" in data and not isinstance(done_status, bool) :
        return jsonify({"error": "Не является bool"}), 400
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

@app.route("/tasks/stats", methods=["GET"])
def get_stats():
    all_tasks = models.get_all_tasks()
    total_tasks = len(all_tasks)
    done_tasks = len([task for task in all_tasks if task["done"] is True])
    pending_tasks = total_tasks - done_tasks
    return jsonify({
        "total": total_tasks,
        "done": done_tasks,
        "pending": pending_tasks
    })

@app.route("/tasks/complete-all", methods=["POST"])
def mass_status_done():
    all_tasks = models.get_all_tasks()
    for task in all_tasks:
            models.update_task(task["id"], done = True)
    all_tasks = models.get_all_tasks()
    return jsonify(all_tasks)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(port=port, debug=debug_mode)
