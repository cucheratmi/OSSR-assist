from flask import render_template
from utils import *

def second_reviewer(project_id):
    return render_template('records_second_reviewer.html', project_id=project_id)