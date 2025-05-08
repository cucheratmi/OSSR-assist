from flask import Flask, render_template, request, redirect, url_for, Response, stream_with_context

from utils import *
from AI_utils import *
from prompts import *


def get_prompt_screening(project_id, source):
    sql = "SELECT eligibility_criteria FROM projects WHERE id=?"
    eligibility_criteria = sql_select_fetchone(sql, (project_id,))['eligibility_criteria']


    if source == "pdf":
        prompt =  prompt_template_screening_pdf.format(eligibility_criteria=eligibility_criteria, context="{context}")
    else:
        prompt = prompt_template_screening_abstract.format(eligibility_criteria=eligibility_criteria, context="{context}")

    return prompt


def evaluate_eligibility(record_id, title, context, prompt, cur, con, source):
    output = ""

    if context is None: context = ""

    output += f"{title}"

    response = ""
    prompt2 = prompt.format(context=context)
    prompt_system = "Your are an expert in clinical trials and systematic review."
    try:
        response = invoke_llm_text_output("primary", prompt2, prompt_system)
    except:
        output += "<p>llm ERROR</p>"

    if response != "":
        decision = 0
        h = response.split("\n")[0].lower().strip()
        if "study is eligible" in h: decision = 1
        if "study is not eligible" in h: decision = -1

        output += " <span style='color: red;'>not eligible</span>" if decision == -1 else " <span style='color: green;'>eligible</span>"

        if record_id > 0:
            response = response.encode("utf-8").decode('utf-8')
            response = response + "\n\nScreening using " + source
            sql = "UPDATE records SET AI_answer=?, AI_decision=? WHERE id=?"
            try:
                cur.execute(sql, (response, decision, record_id))
                con.commit()
            except Exception as e:
                output += " !!! ERROR in writing into database !!! "
                print(e)
                print("\n")

    return output


##### streaming #####

def records_screening_AI(project_id, source):
    return render_template('streaming_screening_AI_window.html',project_id=project_id, source=source)

def screening_AI_stream(project_id, source):

    prompt = get_prompt_screening(project_id, source)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    con2 = sqlite3.connect(DB_PATH)
    cur2 = con2.cursor()

    sql="SELECT id, title, abstract FROM records WHERE project=? AND AI_decision=0"
    cur.execute(sql, (project_id,))

    def generate():
        try:
            for row in cur.fetchall():
                context = None
                if source == "pdf":
                    context = get_pdf(row['id'])
                if source == "abstract" or (source == "pdf" and context is None):
                    context = row['title'] + " " + row['abstract']

                chunk = evaluate_eligibility(row['id'], row['title'], context, prompt, cur2, con2, source)
                yield "data: " + chunk + "\n\n"

            yield 'data: <h4>Completed !</h4>\n\n'
            yield 'data: Stream ended.\n\n'
        finally:
            yield 'data: <h4>Completed !</h4>\n\n'
            yield 'data: Stream ended.\n\n'
            cur.close()
            con.close()
            cur2.close()
            con2.close()

    return Response(stream_with_context(generate()), content_type='text/event-stream')




################## AI accuracy ##############################

def records_AI_screening_doublecheck(project_id):

    def row_to_dict(row):
        abstract = "<p>" + row['title'] + "</p>" + row['abstract']
        AI_answer = row['AI_answer'].replace("\n","<br/>")
        col = "green" if row['selection'] in [InclusionStatus.INCLUDED_FIRST_PASS.value, InclusionStatus.INCLUDED_SECOND_PASS.value] else "red"
        selection_span = f"<h5 style='color: {col}'>{INCLUSION_STATUS_DICT[int(row['selection'])]}</h5>"
        AI_decision_span = "<h5 style='color: green;'>Eligible</h5>" if row['AI_decision'] == 1 else "<h5 style='color: red;'>Not eligible</h5>"
        r = {'abstract': abstract, 'AI_answer': AI_answer, 'id':row['id'], 'selection':selection_span, 'AI_decision':AI_decision_span}
        return r

    def build_table(v_human, AI_decision):
        sin = ','.join([str(x) for x in v_human])
        sql = f"SELECT id, title, abstract, selection, AI_decision, AI_answer FROM records WHERE project=?  AND selection IN ({sin})  AND AI_decision = ?"
        rows = sql_select_fetchall(sql, (project_id, AI_decision,))

        table = []
        for row in rows:
            table.append(row_to_dict(row))
        return table


    v_humain =[InclusionStatus.INCLUDED_FIRST_PASS.value, InclusionStatus.INCLUDED_SECOND_PASS.value]
    table1 = build_table(v_humain, -1)

    v_humain =[InclusionStatus.EXCLUDED_FIRST_PASS.value, InclusionStatus.EXCLUDED_SECOND_PASS.value]
    table2 = build_table(v_humain, 1)

    v_humain =[InclusionStatus.INCLUDED_FIRST_PASS.value, InclusionStatus.INCLUDED_SECOND_PASS.value]
    table3 = build_table(v_humain, 1)

    v_humain =[InclusionStatus.EXCLUDED_FIRST_PASS.value, InclusionStatus.EXCLUDED_SECOND_PASS.value]
    table4 = build_table(v_humain, -1)



    return render_template('AI_doublecheck.html',
                           table1=table1, table2=table2, table3=table3, table4=table4,
                           project_id=project_id)