"""Function to write dataframe to excel

20-12-2022
Arno Kemner
"""
import pandas as pd  # The Pandas data science library


def write_to_excel(df: pd.DataFrame, filepath: str, sheet_name: str, column_formats: dict):
    writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
    df.to_excel(writer, sheet_name=sheet_name, index=False)

    background_color = '#0a0a23'
    font_color = '#ffffff'

    string_template = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    dollar_template = writer.book.add_format(
        {
            'num_format': '$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    integer_template = writer.book.add_format(
        {
            'num_format': '0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    float_template = writer.book.add_format(
        {
            'num_format': '0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    percent_template = writer.book.add_format(
        {
            'num_format': '0.0%',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    for column in column_formats.keys():
        match column_formats[column][1]:
            case 'string':
                template = string_template
            case 'float':
                template = float_template
            case 'percent':
                template = percent_template
            case 'integer':
                template = integer_template
            case 'dollar':
                template = dollar_template
            case _:
                template = string_template

        writer.sheets[sheet_name].set_column(
            f'{column}:{column}', 25, template)
        writer.sheets[sheet_name].write(
            f'{column}1', column_formats[column][0], template)

    writer.close()
