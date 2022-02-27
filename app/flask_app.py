import os
from flask import Flask, send_file, flash, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename
from combination_counter.combination_counter import CombinationCounter
import shutil
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask
    return celery

UPLOAD_FOLDER = 'files_to_process'
ALLOWED_EXTENSIONS = {'xlsx'}

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1000 * 1000
app.config.update(
    CELERY_BROKER_URL=os.environ['REDIS_URL'],
    CELERY_RESULT_BACKEND=os.environ['REDIS_URL']
)
celery = make_celery(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if os.path.exists('files_to_process'):
            shutil.rmtree('files_to_process')
        os.makedirs('files_to_process')
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('load_and_process'))
    return render_template("upload.html")

@celery.task
def background_task():
    for file in os.listdir("files_to_process"):
        if file.endswith(".xlsx"):
            path = file
    counter = CombinationCounter()
    counter.count_combinations(path)

@app.route('/load_and_process')
def load_and_process():
    app.comb_results = background_task.delay()
    return redirect(url_for('download_file'))

@app.route('/download_file', methods=['GET', 'POST'])
def download_file():
    if request.method == 'POST':
        for file in os.listdir("files_to_process"):
            if file.endswith(".csv"):
                return send_file(f"../files_to_process/{file}", as_attachment=True)
        else:
            return redirect(request.url)
    return render_template("download.html")