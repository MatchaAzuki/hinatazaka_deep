import PySimpleGUI as sg

import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
import urllib.parse

def make_one_line_checkbox(csv, indices):
    one_line_layout = []
    
    for index in indices:
        one_line_layout.append(sg.Checkbox(text=csv["full_name"][index], size=(10, 1),
                                           disabled=not csv["visible"][index], key=csv["name"][index]))
    
    return one_line_layout

def make_member_checkbox(csv, n_person_one_line):
    
    def divide_indices_per_element(indices, n_element):
        divide_indices = []

        start_index = 0
        end_index = end_index = min(len(indices), n_element)

        while True:
            divide_indices.append(indices[start_index : end_index])
            start_index = min(len(indices), start_index + n_element)
            end_index = min(len(indices), end_index + n_element)
            if start_index == end_index:
                break
                
        return divide_indices
    
    divide_indices = divide_indices_per_element(csv.index.values, n_person_one_line)
    
    checkboxes = []
    
    for indices in divide_indices:
        checkboxes.append(make_one_line_checkbox(csv, indices))
        
    return checkboxes

if __name__ == "__main__":
    csv = pd.read_csv('hinatazaka_blog.csv', encoding="utf8")

    hours = list(range(24))
    minutes = list(range(60))

    # 日付検索のパターン
    pattern = '\d{4}.\d{1,2}.\d{1,2} \d{2}:\d{2}'
    p = re.compile(pattern)

    # トップページのURL
    hinata_homepage = 'https://www.hinatazaka46.com'

    #  セクション1 - オプションの設定と標準レイアウト
    sg.theme('Default1')

    layout = [
        [sg.Text('取得開始日時')],
        [
            sg.Input('', size=(10, 1), key='start_date'), 
            sg.Spin(values=hours, initial_value=0, size=(2, 1), key='start_hour'), sg.Text("時"),
            sg.Spin(values=minutes, initial_value=0, size=(2, 1), key='start_minute'), sg.Text("分")
        ],
        [sg.CalendarButton('取得開始日を選んでください', 
                        target='start_date', format="%Y/%m/%d", key='start_calendar')],
        
        # empty block
        [sg.Text('')],
        
        [sg.Text('取得終了日時')],
        [
            sg.Input('', size=(10, 1), key='end_date'), 
            sg.Spin(values=hours, initial_value=0, size=(2, 1), key='end_hour'), sg.Text("時"),
            sg.Spin(values=minutes, initial_value=0, size=(2, 1), key='end_minute'), sg.Text("分"),
            sg.Checkbox('now', enable_events=True, key='is_now')
        ],
        [sg.CalendarButton('取得終了日を選んでください', 
                        target='end_date', format="%Y/%m/%d", key='end_calendar')],
        # empty block
        [sg.Text('')],
        
        [
            sg.Input('', size=(50, 1), disabled=True, key='output_folder'),
            sg.FolderBrowse('出力フォルダ指定', initial_folder=os.getcwd(),
                            enable_events=True, target='output_folder', key='select_folder')
        ],
        
        # empty block
        [sg.Text('')],
        
        [sg.Checkbox('ブログタイトルごとに保存する', key='per_title')],
        
        # empty block
        [sg.Text('')],
        
        [sg.Checkbox('ALL', enable_events=True, key='all')]
    ]

    layout.extend(make_member_checkbox(csv, 5))

    layout.append([sg.Text('')])

    layout.append([sg.Button('ダウンロード開始', enable_events=True, key='download')])

    # セクション 2 - ウィンドウの生成
    window = sg.Window('日向坂ブログ画像 ダウンロード', layout)

    # セクション 3 - イベントループ
    while True:
        event, values = window.read()

        if event is None:
            break

        # now ボタンチェックイベント
        if 'is_now' in event:
            is_now = values['is_now']
            window['end_date'].update(disabled=is_now)
            window['end_calendar'].update(disabled=is_now)
            window['end_hour'].update(disabled=is_now)
            window['end_minute'].update(disabled=is_now)

            # 今の時間を指定したなら
            if is_now:
                datetime_now = datetime.datetime.now()
                ymd = datetime_now.strftime("%Y/%m/%d")
                hour = datetime_now.hour
                minute = datetime_now.minute
                window['end_date'].update(ymd)
                window['end_hour'].update(hour)
                window['end_minute'].update(minute)

        # all チェックボックスイベント   
        if 'all' in event:
            all_checked = values['all']
            if all_checked:
                for index in range(len(csv)):
                    if csv['visible'][index]:
                        window[csv['name'][index]].update(True)

        if 'download' in event:
            is_download = True
            
            # 日時チェック
            try:
                start_date_str = values['start_date']
                start_hour = values['start_hour']
                start_minute = values['start_minute']
                std = start_date_str + ' ' + str(start_hour) + ':' + str(start_minute)           
                start_datetime = datetime.datetime.strptime(std, '%Y/%m/%d %H:%M')
                
                end_date_str = values['end_date']
                end_hour = values['end_hour']
                end_minute = values['end_minute']
                end = end_date_str + ' ' + str(end_hour) + ':' + str(end_minute)
                end_datetime = datetime.datetime.strptime(end, '%Y/%m/%d %H:%M')
            except ValueError as ve:
                sg.popup(ve)
                is_download = False
                
            if start_datetime > end_datetime:
                sg.popup('開始日時が終了日時よりも後の日時です')
                is_download = False
            if start_datetime > datetime.datetime.now():
                sg.popup('開始日時が現在時刻よりも後の日時です')
                is_download = False
                
            # 保存フォルダーチェック
            save_top_folder = values['output_folder']
            if not os.path.exists(save_top_folder):
                is_download = False
                sg.popup('指定したフォルダが存在しません')
            elif save_top_folder[-1] != '/':
                save_top_folder = save_top_folder + '/'
            
            # ブログ名ごとに保存するか
            is_save_per_title = values['per_title']
            
            # 保存メンバーチェック
            save_member_index = []
            for index in range(len(csv)):
                if values[csv['name'][index]]:
                    save_member_index.append(index)
            
            # ダウンロード本体
            if is_download:
                # start_date-end_date のフォルダ作成
                day_folder_name = start_datetime.strftime("%Y%m%d_%H%M") + '-' + end_datetime.strftime("%Y%m%d_%H%M")
                save_day_folder = save_top_folder + day_folder_name+ '/'
                os.makedirs(save_day_folder, exist_ok=True)
                
                for (k, index) in enumerate(save_member_index):
                    sg.OneLineProgressMeter('画像保存(メンバーごと)', k+1, len(save_member_index),
                                            'pbar_per_member', csv["full_name"][index])
                    ct = str(csv["ct"][index])
                    member_folder_name = csv["folder_name"][index] + '/'
                    os.makedirs(save_day_folder + member_folder_name, exist_ok=True)

                    page_number = 0

                    while True:
                        blog_list_url = 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&page=' \
                            + str(page_number) + '&cd=member&ct=' + ct
                        soup = BeautifulSoup(requests.get(blog_list_url).text, 'html.parser')

                        # 記事がないページに到達したら抜ける
                        if len(soup.findAll('div', 'p-blog-article')) == 0:
                            break

                        loop = True
                        # 記事本体を取得
                        for article in soup.findAll('div', 'p-blog-article'):
                            # 日付処理
                            date_search = p.search(article.find('div', 'c-blog-article__date').text)
                            datetime_origin_format = date_search.group()
                            date = datetime.datetime.strptime(datetime_origin_format, '%Y.%m.%d %H:%M')

                            # 指定日時範囲よりも前なら終わる
                            if date <= start_datetime:
                                loop = False
                                break
                            # 指定日時範囲よりも後なら何もしない
                            elif date >= end_datetime:
                                continue

                            # タイトル処理
                            title = article.find('div', class_='c-blog-article__title').text
                            title_search = re.search('(\S){1}(.*)', title)

                            # たまに無題のタイトルがあるのでそれ用の対処
                            if title_search is None:
                                title = 'no title'
                            else:
                                title = title_search.group()

                            # url処理
                            article_url = hinata_homepage + article.find('a', class_='c-button-blog-detail').get('href')

                            # article__text 処理
                            article_text = article.find('div', class_='c-blog-article__text')

                            # 1ブログの画像url取得
                            urls = []
                            for link in article_text.find_all("img"):
                                if link.get("src"):
                                    src = link.get("src")
                                    urls.append(src)

                            if is_save_per_title:
                                title = re.sub(r'[\\/:*?"<>|]+','', title) # ファイル名使用不可文字を削除
                                # こさかな対策
                                if len(title) > 100:
                                    title = title[0:99] + '…'
                                save_folder = save_day_folder + member_folder_name + date.strftime("%Y%m%d_%H%M") + '_' + title + '/'
                                os.makedirs(save_folder, exist_ok=True)
                            else:
                                save_folder = save_day_folder + member_folder_name

                            # 画像保存
                            for url in urls:
                                file_path = save_folder + url.split("/")[-2] + "_" + url.split("/")[-1]
                                if not os.path.exists(file_path):
                                    with open(file_path, "wb") as fp:
                                        res = requests.get(url)
                                        fp.write(res.content)
                                        sg.Print(url + '\t->\t' + file_path)

                        page_number = page_number + 1

                        if not loop:
                            break


    # セクション 4 - ウィンドウの破棄と終了
    window.close()