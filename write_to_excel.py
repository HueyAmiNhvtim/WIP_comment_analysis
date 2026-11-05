import xlsxwriter
import json

streamers_list = ["amelia", "watame", "kiara", "pekora"]


def initializing_file_path(streamer):
    streamer_workbook = xlsxwriter.Workbook(f'streamer_excel/{streamer}.xlsx')
    streamer_full_data = streamer_workbook.add_worksheet("Full Data")
    streamer_lang_dis_intervals = streamer_workbook.add_worksheet("Intervals Language Distribution")
    full_data_excel_intialization(streamer_workbook, streamer_full_data, streamer)
    intervals_data_initialization(streamer_workbook, streamer_lang_dis_intervals, streamer)
    streamer_workbook.close()


def full_data_excel_intialization(workbook, worksheet, streamer):
    # Initialize the worksheet's format
    rows_stuff = ["Stream Name", "Viewcount", "Live Chat", "Comment Section"]
    column_stuff = ["Emote Spam", "Other", "En", "Ja", "Total"]
    merge_format = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'center',
        'border': 2
    })
    special_cell_format = workbook.add_format({
        'bg_color': 'red',
        'bold': 1,
        'align': 'center',
        'valign': 'center',
        'border': 2
    })
    special_non_axis_format = workbook.add_format({
        'align': 'center',
        'valign': 'center',
        'border': 2,
        'bg_color': 'red'
    })
    non_axis_format = workbook.add_format({
        'align': 'center',
        'valign': 'center',
        'border': 2
    })
    worksheet.merge_range(0, 0, 0, 1, "", merge_format)
    for column in range(2, len(column_stuff) + 2):
        worksheet.write(0, column, column_stuff[column - 2], merge_format)
    worksheet.set_column(2, 7, len(column_stuff[0]) + 1)
    for row in range(1, 4*30 + 1):
        row_to_put = rows_stuff[row % 4 - 1]
        if row_to_put == "Stream Name":
            row_to_put = f"Stream Name #{round((row - 1) / 4 + 1)}"
            worksheet.merge_range(row, 0, row, 1, row_to_put, special_cell_format)
            # For the stream name
            worksheet.merge_range(row, 2, row, 6, "", special_non_axis_format)
            # For the viewcount
            worksheet.merge_range(row + 1, 2, row + 1, 6, "", merge_format)
        else:
            worksheet.merge_range(row, 0, row, 1, row_to_put, merge_format)
            for column in range(2, 7):
                worksheet.write(row, column, "", non_axis_format)
    return prepare_data_for_excel(workbook, worksheet, streamer, special_cell_format, merge_format)


def prepare_data_for_excel(workbook, worksheet, streamer, name_format, view_format):
    """Load all the data into excel, man, I'm so tired..."""
    data_list = []
    for i in range(30):
        full_data = f"streamer_comments/{streamer}/full_data/{streamer}'s_stream_#{i}_full_data.json"
        with open(full_data, mode="r") as f:
            full_data = json.load(f)
        stream_name_list = [full_data["name"]]
        viewcount_list = [full_data["views"]]
        lc_dict = full_data["live_chat_lang_distributions"]
        comsec_dict = full_data["comment_sections_lang_distributions"]
        lc_lang_distribution_list = [
            lc_dict["emote_spam"],
            lc_dict["other"],
            lc_dict["en"],
            lc_dict["ja"],
            lc_dict["num_extracted_comments"]
        ]
        comsec_lang_dis_list = [
            comsec_dict["emote_spam"],
            comsec_dict["other"],
            comsec_dict["en"],
            comsec_dict["ja"],
            comsec_dict["num_extracted_comments"]
        ]
        data_list.extend([stream_name_list,
                          viewcount_list,
                          lc_lang_distribution_list,
                          comsec_lang_dis_list])
    return load_into_excel(data_list, worksheet, name_format, view_format)


def load_into_excel(data_list, worksheet, name_format, view_format):
    # Data list's length : 120
    for row in range(1, 121):
        for column in range(2, len(data_list[row - 1]) + 2):
            if row % 4 == 1:
                worksheet.write(row, column, data_list[row - 1][column - 2], name_format)
            worksheet.write(row, column, data_list[row - 1][column - 2], view_format)
    return


def intervals_data_initialization(workbook, worksheet, streamer):
    # Initialize the worksheet's format for language intervals
    rows_stuff = ["Stream Name", "Viewcount",
                  "Part 1", "Part 2", "Part3", "Part 4", "Part 5", "Part 6", "Part 7", "Part 8", "Part 9", "Part 10"]
    column_stuff = ["Emote Spam", "Other", "En", "Ja", "Total"]
    merge_format = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'center',
        'border': 2
    })
    special_cell_format = workbook.add_format({
        'bg_color': 'red',
        'bold': 1,
        'align': 'center',
        'valign': 'center',
        'border': 2
    })
    special_non_axis_format = workbook.add_format({
        'align': 'center',
        'valign': 'center',
        'border': 2,
        'bg_color': 'red'
    })
    non_axis_format = workbook.add_format({
        'align': 'center',
        'valign': 'center',
        'border': 2
    })
    worksheet.merge_range(0, 0, 0, 1, "", merge_format)
    for column in range(2, len(column_stuff) + 2):
        worksheet.write(0, column, column_stuff[column - 2], merge_format)
    worksheet.set_column(2, 7, len(column_stuff[0]) + 1)
    for row in range(1, 12 * 30 + 1):
        row_to_put = rows_stuff[row % 12 - 1]
        if row_to_put == "Stream Name":
            row_to_put = f"Stream Name #{round((row - 1) / 12 + 1)}"
            worksheet.merge_range(row, 0, row, 1, row_to_put, special_cell_format)
            # For the stream name
            worksheet.merge_range(row, 2, row, 6, "", special_non_axis_format)
            # For the viewcount
            worksheet.merge_range(row + 1, 2, row + 1, 6, "", merge_format)
        else:
            worksheet.merge_range(row, 0, row, 1, row_to_put, merge_format)
            for column in range(2, 7):
                worksheet.write(row, column, "", non_axis_format)
    return prepare_data_lang_intervals(workbook, worksheet, streamer, special_cell_format, merge_format)


def prepare_data_lang_intervals(worksheet, streamer, name_format, view_format):
    data_list = []
    for i in range(30):
        full_data = f"streamer_comments/{streamer}/full_data/{streamer}'s_stream_#{i}_full_data.json"
        lang_intervals = f"streamer_comments/{streamer}/lang_dis_intervals/{streamer}_stream_#{i}_intervals_lang_distribution.json"
        with open(full_data, mode="r") as f:
            full_data = json.load(f)
        with open(lang_intervals, mode="r") as f:
            lang_intervals_data = json.load(f)
        stream_name_list = [full_data["name"]]
        viewcount_list = [full_data["views"]]
        data_list.extend([stream_name_list, viewcount_list])
        for key, value in lang_intervals_data.items():
            placeholder_list = [
                value["emote_spam"],
                value["other"],
                value["en"],
                value["ja"]
            ]
            data_list.append(placeholder_list)
    return load_into_excel_lang_interval(data_list, worksheet, name_format, view_format)


def load_into_excel_lang_interval(data_list, worksheet, name_format, view_format):
    # Data list's length : 360
    for row in range(1, 361):
        for column in range(2, len(data_list[row - 1]) + 2):
            if row % 12 == 1:
                worksheet.write(row, column, data_list[row - 1][column - 2], name_format)
            worksheet.write(row, column, data_list[row - 1][column - 2], view_format)
        if row % 12 != 1 and row % 12 != 2:
            worksheet.write_formula(f"G{row+1}", f"=SUM(C{row+1}:F{row+1})", view_format)
    return


for streamer in streamers_list:
    initializing_file_path(streamer)
