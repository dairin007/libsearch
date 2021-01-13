import json
import sys
import time
import os
import requests
import re
import mojimoji

RAKUTEN_API = os.environ["RAKUTEN_API"]
CALIL_API = os.environ["CALIL_API"]
LIBRARY_CODE = "Univ_Tohoku"


def get_keys(dict, val):
    return [k for k, v in dict.items() if v == val]


def request_rakuten(keyword, num):
    rakuten_url = "https://app.rakuten.co.jp/services/api/BooksTotal/Search/20170404"
    search_param = set_book_parameter(keyword, num)
    try:
        response = requests.get(rakuten_url, params=search_param)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("error : ", e)
        exit(1)
    result = response.json()
    return result


def set_book_parameter(keyword, hits):
    parameter = {
        "format": "json",
        "keyword": keyword,
        "booksGenreId": "000",
        "applicationId": RAKUTEN_API,
        "hits": hits,
    }
    return parameter


def book_info(result, num):
    bookinfo = []
    try:
        for i in range(num):
            title = mojimoji.zen_to_han(
                json.dumps(result["Items"][i]["Item"]["title"], ensure_ascii=False),
                kana=False,
            )
            author = mojimoji.zen_to_han(
                json.dumps(result["Items"][i]["Item"]["author"], ensure_ascii=False),
                kana=False,
            )
            isbn = json.dumps(result["Items"][i]["Item"]["isbn"], ensure_ascii=False)
            abst = mojimoji.zen_to_han(
                json.dumps(
                    result["Items"][i]["Item"]["itemCaption"], ensure_ascii=False
                ),
                kana=False,
            )
            if 150 < len(abst):
                abst = abst[1:150] + " ......"
            bookinfo.append(
                {
                    "title": title[1:-1],
                    "auther": author[1:-1],
                    "isbn": isbn[1:-1],
                    "abst": abst.replace('"', ""),
                }
            )
    except:
        print(json.dumps(result["Items"], ensure_ascii=False, indent=4))
        exit(1)
    return bookinfo


def set_lib_parameter(con, isbn):
    parameter = {
        "format": "json",
        "isbn": isbn,
        "appkey": CALIL_API,
        "systemid": LIBRARY_CODE,
        "callback": "no",
        "continue": con,
    }
    return parameter


def request_lib(isbn):
    lib_url = "https://api.calil.jp/check"
    search_param = set_lib_parameter(0, isbn)
    try:
        response = requests.get(lib_url, params=search_param)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("error : ", e)
        exit(1)
    result = response.json()
    con = result["continue"]
    while con == 1:
        search_param = set_lib_parameter(con, isbn)
        try:
            response = requests.get(lib_url, params=search_param)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("error : ", e)
            exit(1)
        result = response.json()
        con = result["continue"]
        time.sleep(1)
    return result


def add_status_url(bookinfo, num):
    for i in range(num):
        bookinfo[i]["ok_lib"] = ["none"]
        bookinfo[i]["url"] = "none"
        bookinfo[i]["ng_lib"] = ["none"]
        if bookinfo[i]["isbn"] == "":
            break
        isbn = bookinfo[i]["isbn"]
        rent = request_lib(isbn)
        ok_lib = get_keys(rent["books"][isbn]["Univ_Tohoku"]["libkey"], "貸出可")
        ng_lib = get_keys(rent["books"][isbn]["Univ_Tohoku"]["libkey"], "貸出中")
        if len(ok_lib) == 0 and len(ng_lib) == 0:
            bookinfo[i]["ok_lib"] = ["none"]
            bookinfo[i]["url"] = "none"
            bookinfo[i]["ng_lib"] = ["none"]
        elif len(ok_lib) == 0:
            bookinfo[i]["ok_lib"] = ["none"]
            bookinfo[i]["url"] = rent["books"][isbn]["Univ_Tohoku"]["reserveurl"]
            bookinfo[i]["ng_lib"] = ng_lib
        elif len(ng_lib) == 0:
            bookinfo[i]["ok_lib"] = ok_lib
            bookinfo[i]["url"] = rent["books"][isbn]["Univ_Tohoku"]["reserveurl"]
            bookinfo[i]["ng_lib"] = ["none"]
        else:
            bookinfo[i]["ok_lib"] = ok_lib
            bookinfo[i]["url"] = rent["books"][isbn]["Univ_Tohoku"]["reserveurl"]
            bookinfo[i]["ng_lib"] = ng_lib
    return bookinfo


def print_result(bookinfo, num):
    for i in range(num):
        print(
            "--------------------------------------------------------------------------"
        )
        print(i + 1, "/", num)
        print("title : ", bookinfo[i]["title"])
        print("author : ", bookinfo[i]["auther"])
        print("available : ", ", ".join(bookinfo[i]["ok_lib"]))
        print("unavailable : ", ", ".join(bookinfo[i]["ng_lib"]))
        print("url : ", bookinfo[i]["url"])
        print("abst : ", bookinfo[i]["abst"])


def search(keyword, search_num):
    # print("book search start")
    result = request_rakuten(keyword, search_num)
    hit_num = result["hits"]
    bookinfo = book_info(result, hit_num)
    # print("library search start")
    bookinfo = add_status_url(bookinfo, hit_num)
    return bookinfo


if __name__ == "__main__":
    if not len(sys.argv) == 3:
        print("arg1 is Keyword, arg2 is Number of Search")
        exit(1)
    if 10 < int(sys.argv[2]):
        print("number of search must be less than 10")
        exit(1)
    else:
        keyword = sys.argv[1]
        search_num = int(sys.argv[2])
    search(keyword, search_num)
