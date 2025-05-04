from flask import Flask, render_template, request, redirect, url_for, current_app
from utils import *

from AI_utils import AI_initilization

def setup():
    sql="SELECT * FROM config_variables"
    rs = sql_select_fetchall(sql, ())
    assert rs is not None

    API_KEY = ""
    LLM_NAME = ""
    SECONDARY_API_KEY = ""
    SECONDARY_LLM_NAME = ""
    for e in rs:
        variable = e["variable_name"].strip()
        value = e["value"]

        match variable:
            case "API_KEY":
                API_KEY = value
                current_app.config["API_KEY"] = value
            case "LLM_NAME":
                LLM_NAME = value
                current_app.config["LLM_NAME"] = value
            case "SECONDARY_API_KEY":
                SECONDARY_API_KEY = value
                current_app.config["SECONDARY_API_KEY"] = value
            case "SECONDARY_LLM_NAME":
                SECONDARY_LLM_NAME = value
                current_app.config["SECONDARY_LLM_NAME"] = value

    return render_template("setup.html",
                           LLM_NAME=LLM_NAME, API_KEY=API_KEY,
                           SECONDARY_LLM_NAME=SECONDARY_LLM_NAME, SECONDARY_API_KEY=SECONDARY_API_KEY,
                           config_LLM_NAME=current_app.config["LLM_NAME"], config_API_KEY=current_app.config["API_KEY"],
                           config_SECONDARY_LLM_NAME=current_app.config["SECONDARY_LLM_NAME"], config_SECONDARY_API_KEY=current_app.config["SECONDARY_API_KEY"],
                           app=current_app,)

def setup_update_variable(variable_name, value):
    assert variable_name in ["API_KEY", "LLM_NAME", "SECONDARY_API_KEY", "SECONDARY_LLM_NAME"]

    sql = f"UPDATE config_variables SET value=? WHERE variable_name=?"
    sql_update(sql, (value, variable_name,))
    current_app.config[variable_name] = value.strip()
    print(f"variable {variable_name} updated to {value}")
    AI_initilization(current_app)
    return "", 200


#####  initialization app config  ###############################

def app_config(app):
    llm_name = ""
    second_llm_name = ""
    sql = "SELECT * FROM config_variables"
    rows = sql_select_fetchall(sql, ())
    for row in rows:
        k  = row['variable_name'].strip()
        v  = row['value']
        match k:
            case "LLM_NAME":
                app.config[k] = v
                llm_name = v
            case "SECONDARY_LLM_NAME":
                app.config[k] = v
                second_llm_name = v
            case "API_KEY":
                if llm_name == "openai":
                    os.environ["OPENAI_API_KEY"] = v
                elif llm_name == "claude":
                    os.environ["ANTHROPIC_API_KEY"] = v
                elif llm_name == "deepseek":
                    os.environ["HYPERBOLIC_API_KEY"] = v
                else:
                    os.environ["MISTRAL_API_KEY"] = v
            case "SECONDARY_API_KEY":
                if second_llm_name == "openai":
                    os.environ["OPENAI_API_KEY"] = v
                elif second_llm_name == "claude":
                    os.environ["ANTHROPIC_API_KEY"] = v
                elif second_llm_name == "deepseek":
                    os.environ["HYPERBOLIC_API_KEY"] = v
                else:
                    os.environ["MISTRAL_API_KEY"] = v

    if second_llm_name == "":
        app.config['SECONDARY_LLM_NAME'] = app.config['LLM_NAME']

    # load_dotenv()
    env_path = Path('.env')
    if env_path.exists():
        del os.environ['OPENAI_API_KEY']
        del os.environ['MISTRAL_API_KEY']
        del os.environ['ANTHROPIC_API_KEY']
        del os.environ['HYPERBOLIC_API_KEY']
        load_dotenv()

    AI_initilization(app)

    print("initialization done")

