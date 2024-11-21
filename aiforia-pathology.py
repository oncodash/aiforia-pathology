#!/usr/bin/env python3

import requests

def handle_errors(response):
    if not response.ok:
        print("ERROR")
        print(response.status_code)
        # print(json.dumps(response.headers, indent=4))
        print(response.headers)
        response.raise_for_status()


def post(url, token):
    response = requests.post(
        f"https://api.aiforia.com{url}",
        headers = {'Authorization': f"Bearer {token}"}
    )
    handle_errors(response)
    return response.json()

def get(url, token, params = {}):
    response = requests.get(
        f"https://api.aiforia.com{url}",
        headers = {'Authorization': f"Bearer {token}"},
        params = params
    )
    handle_errors(response)
    return response.json()


def get_token(client_id, client_secret):
    response = requests.post(
        "https://identity.aiforia.com/connect/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    )
    handle_errors(response)
    return response.json()["access_token"]


def fake_get(url, token, params = {}):
    API = {
        "/v2/account/user-subscriptions" : "my_token",
        "/v2/analysis/batches": [
            {"batchId": "1", "name":"B1"},
            {"batchId": "2", "name":"B2"},
        ],
        "/v2/analysis/batches/1/ia-runs": [
            {"iaRunId": "1-1"},
            {"iaRunId": "1-2", "name":"12"},
        ],
        "/v2/analysis/batches/2/ia-runs": [
            {"iaRunId": "2-1"},
            {"iaRunId": "2-2"},
        ],
        "/v2/analysis/ia-runs/1-1/summary": {
            "iaSummary":{"items": [
                {"classLabel":"a"},{"classLabel":"b"},{"classLabel":"c"},{"classLabel":"d"}
            ]}
        },
        "/v2/analysis/ia-runs/1-2/summary": {
            "iaSummary":{"items": [
                {"classLabel":"e"},{"classLabel":"f"},{"classLabel":"g"},{"classLabel":"h", "classAlias": "H"}
            ]}
        },
        "/v2/analysis/ia-runs/2-1/summary": {
            "iaSummary":{"items": [
                {"classLabel":"i"},{"classLabel":"j"},{"classLabel":"k"},{"classLabel":"l"}
            ]}
        },
        "/v2/analysis/ia-runs/2-2/summary": {
            "iaSummary":{"items": [
                {"classLabel":"m"},{"classLabel":"n", "classAlias": "N"},{"classLabel":"o"},{"classLabel":"p", "classAlias": "P"}
            ]}
        },
    }
    return API[url]


def prefix(dct, url):
    res = {}
    name = url.split("/")[-1]
    for k,v in dct.items():
        key = f"{name}.{k}"
        res[key] = v
    return res

def gather_summaries(base):
    batches_url = base+"/batches"
    batches = get(batches_url, token, params)
    for batch in batches:
        batchId = batch["batchId"]
        batch_row = prefix(batch, batches_url)
        # print(batch_row)

        iaruns_url = base+f"/batches/{batchId}/ia-runs"
        iaruns = get(iaruns_url, token, params)
        for iarun in iaruns:
            iaRunId = iarun["iaRunId"]
            iarun_row = prefix(iarun, iaruns_url)
            # print("\t",iarun_row)

            sum_url = base+f"/ia-runs/{iaRunId}/summary"
            summaries = get(sum_url, token, params)
            for summary in summaries["iaSummary"]["items"]:
                sum_row = prefix(summary, sum_url)
                # print("\t\t",sum_row)
                row = {}
                row.update(batch_row)
                row.update(iarun_row)
                row.update(sum_row)
                # print("\t\t\t",row)
                yield row


if __name__ == "__main__":
    import sys
    import pandas as pd
    import argparse


    parser = argparse.ArgumentParser()

    parser.add_argument("client_id",
        help="Client ID token")

    parser.add_argument("client_secret",
        help="Client secret token")

    asked = parser.parse_args()

    token = get_token(asked.client_id, asked.client_secret)
    subscription = get("/v2/account/user-subscriptions", token)
    params = {"subscriptionId": subscription[0]["subscriptionId"]}

    base = "/v2/analysis"

    # get = fake_get

    rows = list(gather_summaries(base))
    df = pd.DataFrame(rows)
    df.to_csv(sys.stdout, index=False)

