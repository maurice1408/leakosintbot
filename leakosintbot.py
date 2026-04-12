# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.1",
#     "polars==1.39.3",
#     "pydantic==2.12.5",
#     "requests==2.33.1",
#     "urllib3==2.6.3",
# ]
# ///

import marimo

__generated_with = "0.23.0"
app = marimo.App(
    width="full",
    css_file="/usr/local/_marimo/custom.css",
    auto_download=["html"],
)


@app.cell
def _():
    import marimo as mo
    import requests
    import polars as pl

    from requests.adapters import HTTPAdapter

    from pydantic import BaseModel, Field, BeforeValidator
    from typing import Optional, List, Any, Annotated

    import urllib.parse
    from urllib3.util import Retry

    retry_strategy = Retry(
        total=5, status_forcelist=[400, 403, 429], backoff_factor=2
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("https://", adapter)
    return BaseModel, mo, pl, session


@app.cell
def _():
    TOKEN = "5719785178:G5kRVmQt"
    return (TOKEN,)


@app.cell
def _(BaseModel):
    class BotResults(BaseModel):
        database_name: str
        data: str
        infoleak: str

    return (BotResults,)


@app.function
async def search(session,
                token: str,
                query: str,
                limit: int = 100,
                lang: str = 'en',
                type: str = 'json',
                bot_name: str = None) -> dict:

    """
    Parameter	Description
    'token'	API token
    'request'	A line with your request or an array of lines with several requests.
    'limit'	Search limit (default 100). The number is from 100 to 10,000. 
            It determines the number of returned results and the search range in the database.
    'lang'	The language code on which there will be the results of the request (by default en ).
    'type'	Type of reporting: json, short, html (By default json).
    'bot_name'	The name of the bot in the format @name 
            (it is necessary to indicate if the bot does not apply to the main group of mirrors).
    """

    url = "https://leakosintapi.com/"

    data ={
            "token": token,
            "request": query,
            "limit": limit      
          }

    resp = session.post(
        url,
        headers={"Content-Type": "application/json"},
        json=data
    )

    print(f"HTTP status code: {resp.status_code}")

    return resp.json()


@app.cell
def _(BotResults):
    def generate_report(bot_results: dict):

        result_list = []

        for database_name in bot_results["List"].keys():

            text = []
            #print(type(text))
            #print(f"Database name: {database_name}")

            if not database_name == "No results found":

                result_meta = {
                    "NumOfDatabase": bot_results.get("NumOfDatabase", 0),
                    "NumOfResults": bot_results.get("NumOfResults", 0),
                    "free_requests_left": bot_results.get("free_requests_left", 0)
                }

                for report_data in bot_results["List"][database_name]["Data"]:

                    for column_name in report_data.keys():
                        text.append(f"{column_name}:  {report_data[column_name]}")

                    text.append("")

                    text_lines = "\n".join(text)

                    d ={
                        "database_name": database_name,
                        "data": text_lines,
                        "infoleak": bot_results["List"][database_name]["InfoLeak"]
                    }

                    m = BotResults.model_validate(d)
                    result_list.append(m)

            else:
                d = {
                    "database_name": "No results found",
                    "data": "",
                    "infoleak": ""
                }
                m = BotResults.model_validate(d)
                result_list.append(m)

                result_meta = {}

            #if len(text)>3500:
            #    text = text[:3500]+text[3500:].split("\n")[0]+"\n\nSome data did not fit this message"

        return result_meta, result_list

    return (generate_report,)


@app.cell
def _(mo):
    res_slider = mo.ui.slider(
        start=0,
        stop=10000,
        step=1000,
        value=1000,
        show_value=True,
        label="Number of results to return",
    )
    res_slider
    return (res_slider,)


@app.cell
def _(mo):
    search_input = mo.ui.text(label="Search String",
                              debounce=True,
                              full_width=True,
                              placeholder="Enter search text and hit Enter or tab ⇥"
                             )
    search_input
    return (search_input,)


@app.cell
async def _(TOKEN, mo, res_slider, search_input, session):
    mo.stop(len(search_input.value.strip()) == 0)

    print(search_input.value)

    with mo.status.spinner(title="Searching...") as _spinner:
        bot_results = await search(session,
                            TOKEN,
                            search_input.value,
                            limit=res_slider.value)
        _spinner.update("Done")
    return (bot_results,)


@app.cell
def _(bot_results, generate_report):
    res_meta, res_list = generate_report(bot_results)
    return res_list, res_meta


@app.cell
def _(mo, res_meta):
    sts = mo.hstack([
        mo.stat(label="Number of Databases", value=res_meta.get("NumOfDatabase", 0)),
        mo.stat(label="Number of Results", value=res_meta.get("NumOfResults", 0)),
        mo.stat(label="Free Requests Remaining", value=res_meta.get("free_requests_left", 0))    
    ])
    return (sts,)


@app.cell
def _(pl, res_list):
    df = pl.DataFrame(res_list)
    return (df,)


@app.cell
def _(df, mo):
    bot_tbl = mo.ui.table(data=df,show_data_types=False,selection="multi")
    return (bot_tbl,)


@app.cell
def _(bot_tbl, mo, sts):
    fnl = mo.vstack([
        sts, bot_tbl
    ])
    fnl
    return


@app.cell
def _(bot_tbl, res_list):
    bookmarks = None
    try:
        if (len(res_list) > 0):
            bookmarks = bot_tbl.value
    except:
        pass
    bookmarks
    return


@app.cell
def _():
    # mo.inspect(bot_results)
    return


@app.cell
def _():
    # res_meta
    return


if __name__ == "__main__":
    app.run()
