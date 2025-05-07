from flask import Flask, send_from_directory, render_template, request, Response, stream_with_context
import time
import webbrowser

from outcomes import *
from projects import *
from studies import *
from records import *
from data import *
from pdfs import *
from extraction_fields import *
from setup import *
from AI_screening import *
from retraction_watch import *
from load_reference_file import *
from setup import app_config
from records_deduplication import records_deduplication

app = Flask(__name__)
app.secret_key = 'OSSR54@#66FRT689H_JGFrf'
app_config(app)


@app.route('/setup')
def endpoint_setup():
    return setup()


@app.route('/setup/update_field/<string:variable_name>', methods=['POST'])
def endpoint_setup_update_variable(variable_name):
    value = request.form[variable_name]
    return setup_update_variable(variable_name, value)


############## outcomes ########################

@app.route('/outcomes/setup/<int:project_id>')
def endpoint_outcomes_setup(project_id):
    return outcomes_setup(project_id)


@app.route('/outcomes/add/<int:project_id>', methods=['POST'])
def endpoint_outcomes_add(project_id):
    return outcomes_add(project_id)


@app.route('/outcomes/delete/<int:outcome_id>', methods=['DELETE'])
def endpoint_outcomes_delete(outcome_id):
    return del_outcomes(outcome_id)


@app.route('/outcomes/field_update/<int:outcome_id>/<string:field_name>', methods=['POST'])
def endpoint_outcomes_field_modif(outcome_id, field_name):
    return outcome_field_update(outcome_id, field_name)


@app.route('/outcomes/edit/<int:outcome_id>/<int:project_id>')
def endpoint_outcome_edit(outcome_id, project_id):
    return outcome_edit(outcome_id, project_id)


@app.route('/outcomes/order/<int:project_id>', methods=['POST'])
def endpoint_outcomes_order(project_id):
    outcomes_order(project_id)
    return '', 204

#
# @app.route('/outcomes/result_update/<int:outcome_id>/<int:study_id>', methods=['POST'])
# def endpoint_outcomes_result_update(outcome_id, study_id):
#     return result_update(outcome_id, study_id)

@app.route('/outcomes/result_update2/<string:variable>/<int:outcome_id>/<int:study_id>', methods=['POST'])
def endpoint_outcomes_result_update2(variable, outcome_id, study_id):
    return result_update2(variable, outcome_id, study_id)


#######################  projects  ##########################
@app.route('/')
def endpoint_home():
    return projects_list()


@app.route('/project/edit/<int:id>')
def endpoint_project_edit(id):
    return project_edit(id)


@app.route('/project/add')
def endpoint_project_add():
    return project_add()


@app.route('/project/delete/<int:id>', methods=['DELETE'])
def endpoint_project_delete(id):
    return project_delete(id)


@app.route('/projects/save/<int:project_id>')
def endpoint_projects_save(project_id):
    return project_save(project_id)


@app.route('/project/update_field/<int:project_id>/<string:field_name>', methods=['POST'])
def endpoint_project_update_field(project_id, field_name):
    value = request.form[field_name]
    return update_field("projects", project_id, field_name, value)


@app.route('/project/update_fields/<int:project_id>')
def endpoint_project_extraction_fields_list(project_id):
    return project_fields_edit(project_id)


@app.route('/project/fields_update_order/<int:project_id>', methods=["POST"])
def endpoint_project_fields_update_order(project_id):
    # new_order = request.get_json(force=True)
    project_fields_update_order(project_id)
    return '', 204


@app.route('/project/load_form')
def endpoint_project_load_form():
    return render_template('project_load_form.html')


@app.route('/project/load_json', methods=['POST'])
def endpoint_project_load_json():
    return project_load_json()


############ table ###################


@app.route('/table/ROB/<int:project_id>')
def endpoint_table_ROB(project_id):
    return table_ROB(project_id)


@app.route('/table/results/<int:project_id>')
def endpoint_table_results(project_id):
    return table_results(project_id)


@app.route('/data/results/csv/<int:project_id>')
def endpoint_data_results_csv(project_id):
    return data_results_csv(project_id)


@app.route('/data/results/excel/<int:project_id>')
def endpoint_data_results_excell(project_id):
    return data_results_excel(project_id)

@app.route('/data/outcomes/short_format/<int:project_id>')
def endpoint_data_outcomes_short_format(project_id):
    return get_outcomes_data_short_format(project_id)



########################### extraction field ############################

@app.route("/extraction_field/edit/<int:field_id>/<int:project_id>")
def endpoint_extraction_field_edit(field_id, project_id):
    return extraction_field_edit(field_id, project_id)


@app.route("/extraction_field/modif/<int:field_id>/<string:field_name>", methods=['POST'])
def endpoint_extraction_field_modif(field_id, field_name):
    return update_field("study_fields", field_id, field_name, request.form[field_name])


@app.route("/extraction_field/add/<int:project_id>")
def endpoint_extraction_field_add(project_id):
    return extraction_field_add(project_id)


@app.route("/extraction_field/delete/<int:field_id>/<int:project_id>", methods=['DELETE'])
def endpoint_extraction_field_delete(field_id, project_id):
    return extraction_field_delete(field_id, project_id)


@app.route("/extraction_field/load_standard_fields/<int:project_id>/<string:file>")
def endpoint_extraction_field_load_standard_fields(file, project_id):
    return load_standard_fields_file(file, project_id)


########################### studies  #####################################

@app.route('/studies/list/<int:project_id>')
def endpoint_studies_list(project_id):
    return studies_list(project_id)


@app.route('/study/edit/<int:study_id>/<int:project_id>')
def endpoint_study_edit(study_id, project_id):
    return study_edit(study_id, project_id)


@app.route('/study_add/<int:project_id>')
def endpoint_study_add(project_id):
    return study_add(project_id)


@app.route('/study/update_field/<int:study_id>/<string:field_name>', methods=['POST'])
def endpoint_study_update_field(study_id, field_name):
    value = request.form[field_name]
    return update_field("studies", study_id, field_name, value)


@app.route('/study/update_field2/<int:study_id>/<int:field_id>', methods=['POST'])
def endpoint_study_update_field2(study_id, field_id):
    return htmlx_update_field2(study_id, field_id, request.form)


@app.route('/study/extraction_AI1/<int:study_id>/<int:record_id>')
def endpoint_study_extraction_AI1(study_id, record_id):
    # TODO à effacer
    return study_extraction_AI1(study_id, record_id)


@app.route('/study_delete/<int:study_id>/<int:project_id>')
def endpoint_study_delete(study_id, project_id):
    return study_delete(study_id, project_id)


@app.route('/study_delete2/<int:study_id>/<int:project_id>', methods=['DELETE'])
def endpoint_study_delete2(study_id, project_id):
    return study_delete2(study_id, project_id)


@app.route('/study/panel1/<int:study_id>/<int:project_id>')
# TODO peut être à effacer
def endpoint_study_panel1(study_id, project_id):
    return study_panel1(study_id, project_id)


@app.route('/study/panel_references/<int:study_id>/<int:project_id>', defaults={'record_id': None})
@app.route('/study/panel_references/<int:study_id>/<int:project_id>/<int:record_id>')
def endpoint_study_panel_references(study_id, project_id, record_id):
    return study_panel_references(study_id, project_id, record_id)


# @app.route('/study/fullscreen_old/<int:study_id>/<int:project_id>/', defaults={'record_id': 0,'tab': 'study'})
# @app.route('/study/fullscreen_old/<int:study_id>/<int:project_id>/<int:record_id>/', defaults={'tab': 'study'})
# @app.route('/study/fullscreen_old/<int:study_id>/<int:project_id>/<int:record_id>/<string:tab>/')
# def endpoint_study_fullscreen_old(study_id, project_id, record_id, tab):
#     return study_fullscreen_old(study_id, project_id, record_id, tab)


@app.route('/study/fullscreen/<string:tab>/<int:study_id>/<int:project_id>/<int:record_id>/', defaults={'AI': 0})
@app.route('/study/fullscreen/<string:tab>/<int:study_id>/<int:project_id>/<int:record_id>/<int:AI>')
def endpoint_study_fullscreen(study_id, project_id, record_id, tab, AI):
    return study_fullscreen(study_id, project_id, record_id, tab, AI)


# TODO deprecated
# @app.route('/study/fullscreen_AI/<int:study_id>/<int:project_id>/', defaults={'record_id': 0})
# @app.route('/study/fullscreen_AI/<int:study_id>/<int:project_id>/<int:record_id>/')
# def endpoint_study_fullscreen_AI(study_id, project_id, record_id):
#     return study_fullscreen_AI(study_id, project_id, record_id)
#
# @app.route('/study/AI_extract/<int:study_id>/<int:record_id>/<int:project_id>/', defaults={'context_source': 'abstract'})
# @app.route('/study/AI_extract/<int:study_id>/<int:record_id>/<int:project_id>/<string:context_source>/')
# def endpoint_study_AI_extract(study_id, record_id, project_id, context_source):
#     return study_extraction_personalised_fields(study_id, record_id, project_id, context_source)
#
# @app.route('/study/AI_ROB/<int:study_id>/<int:record_id>/<int:project_id>/')
# def endpoint_study_AI_ROB(study_id, record_id, project_id):
#     return study_AI_ROB(study_id, record_id, project_id)

@app.route('/study/check_extraction/<int:study_id>/<int:project_id>/<int:record_id>/')
def endpoint_study_check_extraction(study_id, project_id, record_id):
    return study_check_extraction(study_id, project_id, record_id)


@app.route('/study/check_ROB/<int:study_id>/<int:project_id>/<int:record_id>/')
def endpoint_study_check_ROB(study_id, project_id, record_id):
    return study_check_ROB(study_id, project_id, record_id)

@app.route('/study/check_outcomes/<int:study_id>/<int:record_id>/')
def endpoint_study_check_outcomes(study_id, record_id):
    return study_check_outcomes(study_id, record_id)

@app.route('/study/ROB_set_level/<int:study_id>/<int:domain>', methods=['POST'])
def endpoint_study_ROB_set_level(study_id, domain):
    return set_ROB_level(study_id, domain)


@app.route('/study/ROB_set_justification/<int:study_id>/<int:domain>', methods=['POST'])
def endpoint_study_ROB_set_justification(study_id, domain):
    return set_ROB_justification(study_id, domain)


####################### records  ###################################

@app.route('/record/edit/<int:record_id>/<int:project_id>')
def endpoint_record_edit(record_id, project_id):
    return record_edit(record_id, project_id)


@app.route('/record/field_modif/<int:record_id>/<string:field_name>', methods=['POST'])
def endpoint_record_field_modif(record_id, field_name):
    value = request.form[field_name]
    return update_field("records", record_id, field_name, value)


@app.route('/records/AI_doublecheck_results/<int:project_id>')
def endpoint_records_AI_doublecheck_results(project_id):
    return records_AI_screening_doublecheck(project_id)


@app.route("/records/deduplication/<int:project_id>")
def endpoint_records_deduplication(project_id):
    return records_deduplication(project_id)


@app.route('/records/stream_load_reference_file/<int:project_id>/<int:database>/', methods=['GET'])
def endpoint_records_stream_load_reference_file(project_id, database):
    return Response(stream_with_context(read_endnote_export_file(project_id, database)),
                    content_type='text/event-stream')  ## TODO erreur


@app.route('/records/reset_selection/<int:record_id>/<int:project_id>/<int:pass_number>')
def endpoint_record_reset_selection(record_id, project_id, pass_number):
    return reset_selection(record_id, project_id, pass_number)


@app.route('/records/list/<int:project_id>/', defaults={'pass_number': 1, 'page': 1})
@app.route('/records/list/<int:project_id>/<int:pass_number>/', defaults={'page': 1})
@app.route('/records/list/<int:project_id>/<int:pass_number>/<int:page>')
def endpoint_records_list(project_id, pass_number, page):
    return records_list(project_id, pass_number, page)


@app.route('/records/upload/<int:project_id>/<string:s_database>', methods=['POST'])
def endpoint_records_upload(project_id, s_database):
    return records_upload(project_id, s_database)


@app.route('/records/upload_form/<int:project_id>/<string:s_database>')
def endpoint_records_upload_form(project_id, s_database):
    return records_upload_form(project_id, s_database)


@app.route('/records/screening_AI/<int:project_id>')
def endpoint_records_screening_AI(project_id):
    return records_screening_AI(project_id)


@app.route('/records/screening_pass1_window/<int:record_id>/<int:project_id>', )
def endpoint_records_screening_pass1_window(record_id, project_id):
    return records_screening_window(record_id, project_id, 1)


@app.route('/records/screening_pass2_window/<int:record_id>/<int:project_id>', )
def endpoint_records_screening_pass2_window(record_id, project_id):
    return records_screening_window(record_id, project_id, 2)


@app.route('/records/screening_pass1_next/<int:record_id>/<int:project_id>')
def endpoint_records_screening_pass1_next(record_id, project_id):
    return records_screening_pass1_next(record_id, project_id)


@app.route('/records/screening_pass2_next/<int:record_id>/<int:project_id>')
def endpoint_records_screening_pass2_next(record_id, project_id):
    return records_screening_pass2_next(record_id, project_id)


@app.route('/records/study_add/<int:project_id>/<int:record_id>')
def endpoint_record_study_add(project_id, record_id):
    return record_study_add(project_id, record_id)


@app.route('/records/create_study/<int:project_id>/<int:record_id>/<int:pass_number>')
def endpoint_record_create_study(project_id, record_id, pass_number):
    return record_create_study(project_id, record_id, pass_number)


@app.route('/records/screening_included/<int:record_id>/<int:project_id>/<string:selection>/<int:pass_number>')
def endpoint_records_screening_included(record_id, project_id, selection, pass_number):
    return records_screening_set_included(record_id, selection, pass_number, project_id)


@app.route('/records/screening_excluded/<int:record_id>/<int:project_id>/<string:reason>/<int:pass_number>')
def endpoint_records_screening_excluded(record_id, project_id, reason, pass_number):
    return records_screening_set_excluded(record_id, reason, pass_number, project_id)


@app.route('/records/link_record_to_study/<int:record_id>/<int:study_id>')
def endpoint_link_record_to_study(record_id, study_id):
    return link_record_to_study(record_id, study_id, pass_number=1)


@app.route('/records/delete_AI_suggestions/<int:project_id>')
def endpoint_delete_AI_suggestions(project_id):
    return delete_AI_suggestions(project_id)


@app.route('/records/delete/<int:project_id>')
def endpoint_records_delete(project_id):
    return records_delete(project_id)


@app.route('/records/export_CSV/<int:project_id>')
def endpoint_records_export_CSV(project_id):
    return records_export_CSV(project_id)


@app.route('/records/export_RIS/<int:project_id>')
def endpoint_records_export_RIS(project_id):
    return records_export_RIS(project_id)


@app.route('/records/flowchart/<int:project_id>')
def endpoint_records_flowchart(project_id):
    return records_flowchart(project_id)


@app.route('/records/retraction_watch/<int:project_id>')
def endpoint_records_retraction_watch(project_id):
    return retraction_watch(project_id)


#################### data  #######################################

@app.route('/data/list1/<int:project_id>')
def endpoint_data_list1(project_id):
    return data_list1(project_id)


@app.route('/data/csv1/<int:project_id>')
def endpoint_data_csv1(project_id):
    return data_csv1(project_id)


@app.route('/data/excel1/<int:project_id>')
def endpoint_data_excel1(project_id):
    return data_excel1(project_id)


@app.route('/data/ROB/csv1/<int:project>')
def endpoint_data_ROB_csv1_project(project):
    return data_ROB_csv1_project(project)


@app.route('/data/ROB/excel1/<int:project_id>')
def endpoint_data_ROB_excel1(project_id):
    return data_ROB_excel1(project_id)


#################### PDFs  ################################

@app.route('/pdfs/list/<int:project_id>/', defaults={'record_id': 0})
@app.route('/pdfs/list/<int:project_id>/<int:record_id>')
def endpoint_pdfs_list(project_id, record_id):
    return pdfs_list(project_id, record_id)


@app.route('/pdfs/upload_panel/<int:record_id>/<int:project_id>')
def endpoint_pdf_upload_panel(record_id, project_id):
    return pdf_upload_panel(record_id, project_id)


@app.route('/pdfs/upload_pdf/<int:record_id>/<int:project_id>/', defaults={'source': 'pdf'}, methods=['POST'])
@app.route('/pdfs/upload_pdf/<int:record_id>/<int:project_id>/<string:source>', methods=['POST'])
def endpoint_pdf_upload(record_id, project_id, source):
    return pdf_upload(record_id, project_id, source)


@app.route('/pdfs/file/<int:record_id>')
def serve_file(record_id):
    # TODO a déplacer dans PDFs
    try:
        return send_from_directory(PDF_UPLOAD_PATH, f"r{record_id}.pdf")
    except Exception as e:
        return f"Erreur: {str(e)}", 404


###  streaming  #######################################

@app.route('/stream2/<int:project_id>/')
def stream2(project_id):
    return screening_AI_stream(project_id)


# @app.route('/stream')
# def stream():
#     def generate():
#         for i in range(10):
#             yield f'data: Chunk {i}\n\n'
#             time.sleep(1)  # Simulate a delay
#         yield 'data: Stream ended.\n\n'
#
#     return Response(stream_with_context(generate()), content_type='text/event-stream')
#
# @app.route('/test_streaming/')
# def test_streaming():
#     return render_template('streaming_test.html')


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000')
    app.run()
