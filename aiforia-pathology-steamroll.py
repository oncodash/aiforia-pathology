#!/usr/bin/env python3

import requests
import json
import copy

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
        "/v2/analysis/ia-runs/1-1/summary": [
            {"items": [{"classLabel":"a"},{"classLabel":"b"}]},
            {"items": [{"classLabel":"c"},{"classLabel":"d"}]},
        ],
        "/v2/analysis/ia-runs/1-2/summary": [
            {"items": [{"classLabel":"e"},{"classLabel":"f"}]},
            {"items": [{"classLabel":"g"},{"classLabel":"h", "classAlias": "H"}]},
        ],
        "/v2/analysis/ia-runs/2-1/summary": [
            {"items": [{"classLabel":"i"},{"classLabel":"j"}]},
            {"items": [{"classLabel":"k"},{"classLabel":"l"}]},
        ],
        "/v2/analysis/ia-runs/2-2/summary": [
            {"items": [{"classLabel":"m"},{"classLabel":"n", "classAlias": "N"}]},
            {"items": [{"classLabel":"o"},{"classLabel":"p", "classAlias": "P"}]},
        ],
    }
    return API[url]


def amass(rows, url_pivots, i = 0, pivot = None, row = {}, base_url = "", token = "", params = {}):
    # if i == 0:
    #     row = {}
    if i < len(url_pivots)-1:
        print("|   "*i+"i:",i)
        url,next_pivot = url_pivots[i]
        URL = base_url+url.format(pivot)
        name = URL.split("/")[-1]
        print("|   "*i+"url=",url.format(pivot))
        data = get(URL, token, params) # Works even if no format tag {} in `url`
        print("|   "*i+"data=",data)

        for obj in data:
            print("|   "*i+"|   obj:",obj)
            for k,v in obj.items():
                key = f"{name}.{k}"
                # row.pop(key,None)
                row.update({key: v})
            print("|   "*i+"|   row:",row)
            key = obj[next_pivot]
            print("|   "*i+"|   next_pivot:",next_pivot,"=",key)
            amass(rows, url_pivots, i+1, key, row, base_url)

    elif i == len(url_pivots)-1:
        print("|   "*i+"last i:",i)
        url,last_pivot = url_pivots[i]
        URL = base_url+url.format(pivot)
        name = URL.split("/")[-1]
        data = get(URL, token, params) # Works even if no format tag {} in `url`
        print("|   "*i+"data=",data)

        for obj in data:
            last_data = obj[last_pivot]
            print("|   "*i+"|   last_data:",last_data)
            for last_obj in last_data:
                for k,v in last_obj.items():
                    key = f"{name}.{k}"
                    # row.pop(key,None)
                    row.update({key: v})
                print("|   "*i+"|   |   last_row:",row)
                amass(rows, url_pivots, i+1, None, row, base_url)

    else:
        rows.append( copy.copy(row) )
        print("|   "*i+"|   saved:",len(rows))


def steamroll(url_pivots, base_url = "", token = "", params = {}):
    rows = []
    amass(rows, url_pivots, base_url = base_url, params = params)
    for row in rows:
        yield row


if __name__ == "__main__":

    url_pivots = [
        ("/batches", "batchId"),
        ("/batches/{}/ia-runs", "iaRunId"),
        ("/ia-runs/{}/summary", "items")
    ]

    get = fake_get
    for row in steamroll(url_pivots, base_url = "/v2/analysis", token = "", params = {"subscriptionId": "whatever"}):
        print(row)

