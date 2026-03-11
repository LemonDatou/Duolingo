import threading
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global lock to ensure only one script runs at a time
is_running = False
task_lock = threading.Lock()

def execute_task(task_type, param_value):
    global is_running
    try:
        if task_type == "lesson":
            print(f"\n[BackgroundTask] Starting lesson task: loops={param_value}")
            print("🚀 Launching Playwright script...")
            result = subprocess.run(["python3", "duolingo.py", "-c", str(param_value)])
            
            if result.returncode == 0:
                print("[BackgroundTask] 🎉 Lesson task finished successfully.")
            else:
                print("⚠️ Playwright script exited unexpectedly.")

        elif task_type == "xp":
            print(f"\n[BackgroundTask] Starting XP farming task: target={param_value} XP")
            print("🚀 Launching XP farming script...")
            result = subprocess.run(["python3", "duolingo-xp.py", "-t", str(param_value)])
            
            if result.returncode == 0:
                print("[BackgroundTask] 🎉 XP farming finished successfully.")
            else:
                print("⚠️ XP farming script exited unexpectedly.")

    except Exception as e:
        print(f"💥 A critical error occurred in the background task: {e}")
        
    finally:
        # Releasing lock, ready for new tasks
        with task_lock:
            is_running = False
            print("🟢 Worker is idle and ready to accept new tasks.")

def try_start_task(task_type, param_value):
    global is_running
    with task_lock:
        if is_running:
            return False # Busy, rejecting new task
        is_running = True # Idle, locking status
        
    # Starting a background thread to execute the task
    threading.Thread(target=execute_task, args=(task_type, param_value), daemon=True).start()
    return True

# --- API 1: Lesson Runner ---
@app.route('/run-lesson', methods=['POST'])
def run_lesson():
    data = request.get_json(silent=True) or {}
    loop_count = data.get('loop_count', 1)
    
    if try_start_task("lesson", loop_count):
        return jsonify({
            "status": "started", 
            "message": "Lesson task has been accepted and is running in the background...", 
            "loop_count": loop_count
        }), 202
    else:
        return jsonify({"status": "busy", "message": "A task is already running. Please try again later!"}), 429

# --- API 2: XP Farmer ---
@app.route('/run-xp', methods=['POST'])
def run_xp():
    data = request.get_json(silent=True) or {}
    target_xp = data.get('target_xp', 2000)
    
    if try_start_task("xp", target_xp):
        return jsonify({
            "status": "started", 
            "message": "XP farming task has been accepted and is running in the background...", 
            "target_xp": target_xp
        }), 202
    else:
        return jsonify({"status": "busy", "message": "A task is already running. Please try again later!"}), 429

if __name__ == '__main__':
    print("🌐 Duolingo local API service started, listening on 127.0.0.1:15010...")
    app.run(host='127.0.0.1', port=15010)