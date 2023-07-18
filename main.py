import glob
import os
import subprocess

import flet as ft
from mutagen import File

compress_cancellation = False
global root_folder


def main(page: ft.Page):
    global compress_cancellation

    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.path:
            global root_folder
            root_folder = e.path
            selected_files_paths.clear()
            selected_files.clean()
            files = glob.glob(f'{e.path}/*.mp3') + glob.glob(f'{e.path}/*.wav')
            operation_label.value = 'Выбранные файлы'
            selected_files_counter = 0
            cut.disabled = False
            compress_button.disabled = False
            bitrate_dropdown.disabled = False
            for f in files:
                name = os.path.basename(f)
                selected_files_counter += 1
                selected_files.controls.append(ft.Text(f'{selected_files_counter}. {name}'))
                selected_files_paths.append(f)
            page.update()
        else:
            operation_label.value = f'Отменено!'
            operation_label.update()

    def start_operation():
        result_path = f'{root_folder}/fragment'
        if not os.path.exists(result_path):
            os.mkdir(result_path)
        global compress_cancellation
        selected_files.visible = False
        operation_label.value = None
        open_files_button.disabled = True
        compress_button.disabled = True
        cut.disabled = True
        bitrate_dropdown.disabled = True
        length_cut_minutes.disabled = True
        length_cut_seconds.disabled = True
        compress_cancel_button.disabled = False
        compress_cancel_button.color = ft.colors.RED
        page.update()
        counter = 0
        amount = len(selected_files_paths)
        pb_container.content = ft.ProgressBar(width=float('inf'), value=0.0)
        pb_container.content.value = 0
        pb_operation_label_percent.value = f'{round(pb_container.content.value * 100, 2)}%'
        pb_container.update()
        pb_operation_label_percent.update()
        clip_operation_state = cut.value
        compress_cancel_button.disabled = False
        for path in selected_files_paths:
            if compress_cancellation:
                compress_cancellation = False
                operation_label.value = 'Выбранные файлы:'
                pb_operation_label.value = f'Сжатие отменено!'
                open_files_button.disabled = False
                compress_button.disabled = False
                cut.disabled = False
                bitrate_dropdown.disabled = False
                if not cut.value:
                    length_cut_minutes.disabled = True
                    length_cut_seconds.disabled = True
                selected_files.visible = True
                compress_cancel_button.disabled = True
                pb_container.content.visible = False
                pb_operation_label_percent.value = None
                page.update()
                return
            else:
                destination_path = f'{result_path}/{os.path.splitext(os.path.basename(path))[0]}.mp3'
                counter += 1
                with open(path, 'rb') as f:
                    input_mp3 = f.read()
                if clip_operation_state:
                    pb_operation_label.value = f'Обрезка: {os.path.basename(path)} ({counter}/{amount})'
                    pb_operation_label.update()
                    time = int(length_cut_minutes.value) * 60 + int(length_cut_seconds.value)
                    input_mp3 = subprocess.run(['/usr/local/bin/ffmpeg', '-ss', '00:00:00', '-i', '-', '-t',
                                                f'{time}', '-f', 'mp3', '-'], input=input_mp3,
                                               check=True,
                                               capture_output=True).stdout
                pb_operation_label.value = f'Сжатие: {os.path.basename(path)} ({counter}/{amount})'
                pb_operation_label.update()
                subprocess.run(
                    ['/usr/local/bin/ffmpeg', '-i', '-', '-b:a', f'{bitrate_dropdown.value}k', '-f', 'mp3',
                     f'{destination_path}',
                     '-y'],
                    input=input_mp3)
                pb_operation_label.value = f'Восстановление Тегов: {os.path.basename(path)} ({counter}/{amount})'
                pb_operation_label.update()
                src_tags = File(path)
                dst_file = File(destination_path)
                dst_file.update(src_tags, copy=True, delete=True)
                dst_file.save()
                pb_container.content.value = counter * (1.0 / amount)
                pb_operation_label_percent.value = f'{round(pb_container.content.value * 100, 2)}%'
                page.update()
        pb_operation_label.value = f'Сжатие завершено!'
        pb_operation_label.update()
        compress_cancel_button.color = ft.colors.GREY_600
        compress_cancel_button.update()
        compress_cancel_button.disabled = True
        compress_cancel_button.update()
        open_files_button.disabled = False
        compress_button.disabled = False
        cut.disabled = False
        bitrate_dropdown.disabled = False
        length_cut_minutes.disabled = False
        length_cut_seconds.disabled = False
        selected_files.visible = True
        page.update()

    def compress_cancellation_start():
        global compress_cancellation
        pb_operation_label.value = f'Отмена сжатия...'
        compress_cancel_button.color = ft.colors.GREY_600
        compress_cancel_button.update()
        pb_operation_label.update()
        compress_cancel_button.disabled = True
        compress_cancel_button.update()
        compress_cancellation = True
        pb_container.content.value = None
        pb_operation_label_percent.value = None
        page.update()

    def enable_cut():
        if cut.value:
            length_cut_minutes.disabled = False
            length_cut_seconds.disabled = False
        else:
            length_cut_minutes.disabled = True
            length_cut_seconds.disabled = True
        length_cut_minutes.update()
        length_cut_seconds.update()

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    selected_files = ft.ListView(
        expand=True,
        spacing=10,
        height=384,
        width=float('inf'))
    operation_label = ft.Text()
    selected_files_paths = []
    bitrate_dropdown = ft.Dropdown(
        width=100,
        options=[
            ft.dropdown.Option('64'),
            ft.dropdown.Option('128'),
            ft.dropdown.Option('192'),
            ft.dropdown.Option('320'),
        ],
        value='64',
        label='Битрейт',
        disabled=True
    )
    page.overlay.append(pick_files_dialog)
    cut = ft.Checkbox(
        label='Обрезать до:',
        value=False,
        on_change=lambda _: enable_cut(),
        disabled=True
    )
    length_cut_minutes = ft.TextField(
        width=60,
        height=70,
        max_length=2,
        counter_text=" ",
        content_padding=0,
        filled=True,
        text_align=ft.TextAlign.CENTER,
        text_size=25,
        value='1',
        disabled=True
    )
    length_cut_seconds = ft.TextField(
        width=60,
        height=70,
        max_length=2,
        counter_text=" ",
        content_padding=0,
        filled=True,
        text_align=ft.TextAlign.CENTER,
        text_size=25,
        value='30',
        disabled=True

    )
    open_files_button = ft.ElevatedButton(
        'Открыть файлы',
        icon=ft.icons.UPLOAD_FILE,
        on_click=lambda _: pick_files_dialog.get_directory_path(),
    )
    compress_button = ft.ElevatedButton(
        'Сжать',
        icon=ft.icons.COMPRESS,
        on_click=lambda _: start_operation(),
        disabled=True
    )
    compress_cancel_button = ft.ElevatedButton(
        'Отмена',
        icon=ft.icons.CANCEL,
        on_click=lambda _: compress_cancellation_start(),
        disabled=True,

    )
    page.theme = ft.Theme(color_scheme_seed='green')
    pb_container = ft.Container()
    pb_operation_label = ft.Text()
    pb_operation_label_percent = ft.Text()
    page.add(
        ft.Row(
            [
                open_files_button,
                ft.VerticalDivider(),
                ft.Row([compress_button, bitrate_dropdown, compress_cancel_button]),
                ft.VerticalDivider(),
                cut,
                ft.Row([
                    ft.Container(length_cut_minutes, margin=ft.margin.only(top=25)),
                    ft.Container(ft.Text(':', size=50), margin=ft.margin.only(bottom=10)),
                    ft.Container(length_cut_seconds, margin=ft.margin.only(top=25))
                ])

            ],
        ),
        ft.Row(controls=[
            pb_operation_label_percent,
        ],
            alignment=ft.MainAxisAlignment.CENTER),
        pb_container,
        ft.Row(controls=[
            pb_operation_label
        ],
            alignment=ft.MainAxisAlignment.CENTER),
        ft.Row(controls=[
            operation_label,
        ]),
        ft.Container(ft.Stack([
            selected_files,
        ])),
    )


if __name__ == '__main__':
    ft.app(target=main)
