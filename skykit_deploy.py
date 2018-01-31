import time
import subprocess
import sys
import os

backend_start_cmd = ['java', '-jar',
                     'skykit-designer-web-api.jar',
                     '--server.port=8081']
backend_app_name = "DesignerWebApiApplication"
backend_pid_file_name = "backend.pid"

frontend_start_cmd = ['java', '-jar',
                      'skykit-designer-web.jar',
                      '--server.use-forward-headers=true',
                      '--server.port=8082',
                      '--baseURL=skykit-dev.one-sky.ro/backend']
frontend_app_name = "DesignerWebApplication"
frontend_pid_file_name = "frontend.pid"


def start_spring_app(cmd, spring_app_name, pid_file_name):

    app_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    app_pid = app_process.pid

    has_errors = False
    spring_app_started = False
    error_msg = ""

    t_end = time.time() + 45

    for line in app_process.stdout:
        log_line = line.decode('UTF-8')
        if 'ERROR' in log_line:
            error_msg = log_line
            has_errors = True
        if 'Started {}'.format(spring_app_name) in log_line:
            spring_app_started = True
            break
        if time.time() > t_end:
            break

    if spring_app_started and has_errors:
        print("Cannot continue deployment due to errors during spring initialization")
        app_process.kill()
        sys.exit(error_msg)
    elif spring_app_started and not has_errors:
        create_pid_file(app_pid, pid_file_name)
        print("{} has been started successfully".format(spring_app_name))
    elif not spring_app_started and has_errors:
        print("Cannot continue deployment due to errors during spring initialization")
        sys.exit(error_msg)
    else:
        print("Unknown condition")


def create_pid_file(pid, pid_file_name):
    f = open(pid_file_name, "w+")
    f.write("{}".format(pid))
    f.close()


def get_pid(pid_file_name):
    pid = ""
    f = open(pid_file_name, "r")
    for line in f:
        pid = line.strip()
    f.close()
    return pid


# start the backend application first

if not os.path.isfile(backend_pid_file_name):
    print("Cannot find {} file".format(backend_pid_file_name))
    start_spring_app(backend_start_cmd, backend_app_name, backend_pid_file_name)
else:
    current_pid = get_pid(backend_pid_file_name)
    print("Stopping previous version of the application [{}]".format(current_pid))
    subprocess.run(["kill", "-SIGTERM", current_pid])
    start_spring_app(backend_start_cmd, backend_app_name, backend_pid_file_name)

# start the front-end container

if not os.path.isfile(frontend_pid_file_name):
    print("Cannot find {} file".format(frontend_pid_file_name))
    start_spring_app(frontend_start_cmd, frontend_app_name, frontend_pid_file_name)
else:
    current_pid = get_pid(frontend_pid_file_name)
    print("Stopping previous version of the application [{}]".format(current_pid))
    subprocess.run(["kill", "-SIGTERM", current_pid])
    start_spring_app(frontend_start_cmd, frontend_app_name, frontend_pid_file_name)
