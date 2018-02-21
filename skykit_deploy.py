import fileinput
import shutil
import time
import subprocess
import sys
import os

designer_backend_start_cmd = ['java', '-jar',
                     'skykit-designer-web-api.jar',
                     '--server.port=8081']
designer_backend_app_name = "DesignerWebApiApplication"
designer_backend_pid_file_name = "backend.pid"

designer_frontend_start_cmd = ['java', '-jar',
                      'skykit-designer-web.jar',
                      '--server.use-forward-headers=true',
                      '--server.port=8082',
                      '--baseURL=skykit-dev.one-sky.ro/backend',
                      '--previewURL=http://preview-dev.one-sky.ro/backend',
                      '--buildNumber={}'.format(sys.argv[1])]
designer_frontend_app_name = "DesignerWebApplication"
designer_frontend_pid_file_name = "frontend.pid"

trajectory_srv_start_cmd = ['java', '-jar',
                     'skykit-trajectory-generator-server.jar',
                     '--server.port=8084']
trajectory_srv_app_name = "TrajectoryGeneratorServerApplication"
trajectory_srv_pid_file_name = "trajectory_server.pid"

preview_backend_start_cmd = ['java', '-jar',
                     'skykit-preview-web-api.jar',
                     '--server.port=8083']
preview_backend_app_name = "PreviewWebApiApplication"
preview_backend_pid_file_name = "preview_backend.pid"

app_config_js_name = 'skykit-config.js'

old_preview_backend_api_url = 'http://localhost:8070/skykit-api'
new_preview_backend_api_url = 'http://preview-dev.one-sky.ro/backend/skykit-api'

apache_app_path = '/var/www/html/preview-dev/'
apache_app_name = 'preview-web-ui'

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


def replace_in_file(file_path, old_val, new_val):
    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace(old_val, new_val), end='')

def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def clean_folder(path):
    if not os.path.isdir(path):
        raise FileNotFoundError('The {} does not exist'.format(path))

    for root, dirs, files in os.walk(apache_app_path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def deploy_app():
    if not os.path.isdir(apache_app_name):
        raise FileNotFoundError('The {} does not exist'.format(apache_app_name))

    cfg_file = os.path.join(apache_app_name, app_config_js_name)

    if not os.path.isfile(cfg_file):
        raise FileNotFoundError('The {} does not exist'.format(cfg_file))

    if os.path.isdir('{}.old'.format(apache_app_name)):
        shutil.rmtree('{}.old'.format(apache_app_name))

    # make a backup of the existing folder
    copytree(apache_app_name, '{}.old'.format(apache_app_name))

    try:
        clean_folder(apache_app_path)
    except PermissionError as e:
        print('You do not have permission to delete {}. Run with sudo'.format(apache_app_path))

    # update the url in config
    replace_in_file(cfg_file, old_preview_backend_api_url, new_preview_backend_api_url)

    # copy the app to apache folder
    copytree(apache_app_name, apache_app_path)

    shutil.rmtree(apache_app_name)


# start the designer backend application first

if not os.path.isfile(designer_backend_pid_file_name):
    print("Cannot find {} file".format(designer_backend_pid_file_name))
    start_spring_app(designer_backend_start_cmd, designer_backend_app_name, designer_backend_pid_file_name)
else:
    current_pid = get_pid(designer_backend_pid_file_name)
    print("Stopping previous version of the application [{}]".format(current_pid))
    subprocess.run(["kill", "-SIGTERM", current_pid])
    start_spring_app(designer_backend_start_cmd, designer_backend_app_name, designer_backend_pid_file_name)

# start the designer front-end container

if not os.path.isfile(designer_frontend_pid_file_name):
    print("Cannot find {} file".format(designer_frontend_pid_file_name))
    start_spring_app(designer_frontend_start_cmd, designer_frontend_app_name, designer_frontend_pid_file_name)
else:
    current_pid = get_pid(designer_frontend_pid_file_name)
    print("Stopping previous version of the application [{}]".format(current_pid))
    subprocess.run(["kill", "-SIGTERM", current_pid])
    start_spring_app(designer_frontend_start_cmd, designer_frontend_app_name, designer_frontend_pid_file_name)


# start the trajectory server

if not os.path.isfile(trajectory_srv_pid_file_name):
    print("Cannot find {} file".format(trajectory_srv_pid_file_name))
    start_spring_app(trajectory_srv_start_cmd, trajectory_srv_app_name, trajectory_srv_pid_file_name)
else:
    current_pid = get_pid(trajectory_srv_pid_file_name)
    print("Stopping previous version of the application [{}]".format(current_pid))
    subprocess.run(["kill", "-SIGTERM", current_pid])
    start_spring_app(trajectory_srv_start_cmd, trajectory_srv_app_name, trajectory_srv_pid_file_name)

# start the preview backend container

if not os.path.isfile(preview_backend_pid_file_name):
    print("Cannot find {} file".format(preview_backend_pid_file_name))
    start_spring_app(preview_backend_start_cmd, preview_backend_app_name, preview_backend_pid_file_name)
else:
    current_pid = get_pid(preview_backend_pid_file_name)
    print("Stopping previous version of the application [{}]".format(current_pid))
    subprocess.run(["kill", "-SIGTERM", current_pid])
    start_spring_app(preview_backend_start_cmd, preview_backend_app_name, preview_backend_pid_file_name)


# deploy the static angular application
deploy_app()