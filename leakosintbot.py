# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx-retries==0.5.0",
#     "logfire[httpx]==4.32.1",
#     "marimo>=0.25.1",
#     "polars>=2.0.0",
#     "pydantic==2.14.0",
#     "requests==2.33.1",
#     "urllib3==2.6.3",
#     "python-dotenv>=1.1.1",
#     "httpxyz>=0.42.1",
#     "mohtml>=0.1.11",
# ]
# ///

import marimo

__generated_with = "0.26.0"
app = marimo.App(
    width="full",
    app_title="leakosintbot",
    auto_download=["html"],
)


@app.cell
def _():
    import marimo as mo
    import httpxyz
    import polars as pl
    import time

    from httpx_retries import RetryTransport
    from httpx_retries import Retry

    from pydantic import BaseModel, Field, BeforeValidator
    from typing import Optional, List, Any, Annotated

    from dotenv import dotenv_values
    from dataclasses import dataclass

    # import urllib.parse
    # from urllib3.util import Retry

    import asyncio

    import logging
    from logging import basicConfig, getLogger

    from mohtml import div, h1

    return (
        BaseModel,
        Retry,
        RetryTransport,
        basicConfig,
        dataclass,
        div,
        dotenv_values,
        getLogger,
        h1,
        httpxyz,
        logging,
        mo,
        pl,
        time,
    )


@app.cell
def _(logging):
    logging.basicConfig(
        format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )


@app.cell
def _(div, h1):
    div(
        h1(
            f"Leakosintbot",
            align="center",
            style="background-color: DodgerBlue;font-size: 2em",
        )
    )


@app.cell
def _(dataclass, dotenv_values):
    env_settings = dotenv_values(".env")

    @dataclass
    class Settings:
        api_key: str = env_settings["TOKEN"]
        logfire_token: str = env_settings["LOGFIRE_TOKEN"]

    settings = Settings()
    return (settings,)


@app.cell
def _(Retry, RetryTransport, basicConfig, getLogger, httpxyz, settings):
    import logfire

    _lf = logfire.configure(
        token=settings.logfire_token, service_name="leakosintbot"
    )

    basicConfig(handlers=[logfire.LogfireLoggingHandler()])

    logfire.instrument_httpx(
        capture_request_body=True,
        capture_response_body=False,
        capture_headers=True,
    )

    request_duration = logfire.metric_histogram(
        "request_duration",
        unit="ms",
        description="Duration of call to leakosingbot",
    )

    requests_sent = logfire.metric_counter(
        name="requests_sent",
        unit="1",
        description="leakosinbot requests count",
    )

    logger = getLogger(__name__)

    retry_strategy = Retry(
        total=5, status_forcelist=[400, 403, 429], backoff_factor=2
    )

    transport = RetryTransport(retry=retry_strategy)

    client = httpxyz.Client(transport=transport, timeout=60)
    return client, logfire, logger, request_duration


@app.cell
def _(BaseModel):
    class BotResults(BaseModel):
        database_name: str
        data: str
        infoleak: str

    return (BotResults,)


@app.cell
def search(httpxyz, logfire, logger, request_duration, time):
    async def search(
        client,
        token: str,
        query: str,
        limit: int = 100,
        lang: str = "en",
        type: str = "json",
        bot_name: str = None,
    ) -> dict:
        """
        Parameter	Description
        'token'	    API token
        'request'	A line with your request or an array of lines with several requests.
        'limit'	    Search limit (default 100). The number is from 100 to 10,000.
                    It determines the number of returned results and the search range in the database.
        'lang'	    The language code on which there will be the results of the request (by default en ).
        'type'	    Type of reporting: json, short, html (By default json).
        'bot_name'	The name of the bot in the format @name
                    (it is necessary to indicate if the bot does not apply to the main group of mirrors).
        """

        url = "https://leakosintapi.com/"

        data = {"token": token, "request": query, "limit": limit}

        logfire.debug("Data: {data=!r}", data=data)

        try:
            start = time.perf_counter()

            resp = client.post(
                url, headers={"Content-Type": "application/json"}, json=data
            )
            # requests_sent.add(1)
            duration_ms = (time.perf_counter() - start) * 1000
            request_duration.record(duration_ms)

        except httpxyz.ReadTimeout as exc:
            logger.error("Request timed out")

        print(f"HTTP status code: {resp.status_code}")

        return resp.json()

    return (search,)


@app.cell
def _(BotResults, logfire):
    def generate_report(bot_results: dict):

        result_list = []

        for database_name in bot_results["List"].keys():
            text = []
            # print(type(text))
            # print(f"Database name: {database_name}")

            if not database_name == "No results found":
                for report_data in bot_results["List"][database_name]["Data"]:
                    for column_name in report_data.keys():
                        text.append(
                            f"{column_name}:  {report_data[column_name]}"
                        )

                    text.append("")

                    text_lines = "\n".join(text)

                    d = {
                        "database_name": database_name,
                        "data": text_lines,
                        "infoleak": bot_results["List"][database_name][
                            "InfoLeak"
                        ],
                    }

                    m = BotResults.model_validate(d)
                    result_list.append(m)

            else:
                logfire.error("No results returned")
                d = {
                    "database_name": "No results found",
                    "data": "",
                    "infoleak": "",
                }
                m = BotResults.model_validate(d)
                result_list.append(m)

            # if len(text)>3500:
            #    text = text[:3500]+text[3500:].split("\n")[0]+"\n\nSome data did not fit this message"
        result_meta = {
            "NumOfDatabase": bot_results.get("NumOfDatabase", 0),
            "NumOfResults": bot_results.get("NumOfResults", 0),
            "free_requests_left": bot_results.get("free_requests_left", 0),
            "price": bot_results.get("price", 0),
            "search time": bot_results.get("search time", 0),
        }

        logfire.debug("Query: {meta=!r}", meta=result_meta)

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
    search_input = mo.ui.text(
        label="Search String",
        debounce=True,
        full_width=True,
        placeholder="Enter search text and hit ↩️ Enter or tab ⇥",
    )
    search_input
    return (search_input,)


@app.cell
async def _(client, mo, res_slider, search, search_input, settings):
    mo.stop(len(search_input.value.strip()) == 0)

    print(search_input.value)

    with mo.status.spinner(title="Searching...") as _spinner:
        bot_results = await search(
            client,
            settings.api_key,
            search_input.value,
            limit=res_slider.value,
        )
        _spinner.update("Done")
    return (bot_results,)


@app.cell
def _():
    return


@app.cell
def _(bot_results, generate_report, mo, search_input):
    _no_res = None
    no_results_found = False

    res_meta, res_list = generate_report(bot_results)

    if (len(res_list) == 1) and res_list[
        0
    ].database_name.lower() == "no results found":
        _no_res = mo.md(f"""
        /// admonition | Note
            type: warning

        No results found for: {search_input.value}
        ///
        """)

        no_results_found = True

    _no_res
    return no_results_found, res_list, res_meta


@app.cell
def _(mo, res_meta):
    sts = mo.hstack(
        [
            mo.stat(
                label="Number of Databases",
                value=res_meta.get("NumOfDatabase", 0),
            ),
            mo.stat(
                label="Number of Results",
                value=res_meta.get("NumOfResults", 0),
            ),
            mo.stat(
                label="Free Requests Remaining",
                value=res_meta.get("free_requests_left", 0),
            ),
            mo.stat(label="Price", value=res_meta.get("price", 0)),
            mo.stat(label="Search Time", value=res_meta.get("search time", 0)),
        ],
        justify="center",
        gap="2rem",
    )
    return (sts,)


@app.cell
def _(mo, no_results_found, pl, res_list):
    mo.stop(no_results_found)
    df = pl.DataFrame(res_list)
    return (df,)


@app.cell
def _(df, mo):
    bot_tbl = mo.ui.table(data=df, show_data_types=False, selection="multi")
    return (bot_tbl,)


@app.cell
def _(bot_tbl, mo, sts):
    fnl = mo.vstack([sts, bot_tbl])
    fnl


@app.cell
def _(bot_tbl, res_list):
    bookmarks = None
    try:
        if len(res_list) > 0:
            bookmarks = bot_tbl.value
    except:
        pass
    bookmarks


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
