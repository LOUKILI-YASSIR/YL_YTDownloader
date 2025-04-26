from customtkinter import *
from CTkMessagebox import *
from PIL import Image
import webbrowser as wb
from pytube import YouTube as yt
from os import remove, path, rename
from requests import get as get_url
from datetime import timedelta as td
from tkinter import filedialog

# Global constants
IMAGE_DOWNLOAD_PATH = "./downloads/images"
DOWNLOAD_PATH = "./downloads"

def get_title_video(lien_video):
    if any(char in lien_video.title for char in list("""|*:<>"?/\"""")):
        for i in range(len(lien_video.title)):
            if title_video[i] in list("""|*:<>"?/\""""):
                title_video = title_video.replace(title_video[i], " ")
    return title_video

def calc_time(time):
    time = td(seconds=time)
    time_day, time_hour, time_minute, time_second = (
        time.days,
        time.seconds // 3600,
        (time.seconds % 3600) // 60,
        time.seconds % 60,
    )
    if time_day == 0:
        if time_hour == 0:
            return f"{time_minute}:{time_second:02}"
        return f"{time_hour}:{time_minute:02}:{time_second:02}"
    return f"{time_day}:{time_hour:02}:{time_minute:02}:{time_second:02}"

def link_yt():
    wb.open("https://www.youtube.com/")

def value_dropdown_list():
    global list_form_video
    global lien_video
    lien_video=yt(input_link.get())
    print("obj:",lien_video)
    print("Available streams:")
    for stream in lien_video.streams:
        print(stream)


    list_item_yt_video=lien_video.streams.all()   

    video_audio_list = [[], []]
    for i in range(2):
        for resolution in list_form_video:
            if any(
                resolution == stream.resolution and video_extension[i] in stream.mime_type
                for stream in list_item_yt_video
            ):
                for res in list_form_video[list_form_video.index(resolution) :]:
                    video_audio_list[i].append(f"{video_extension[i]} - {res}")
                break
    list_video_audio_resolution = video_audio_list[0] + video_audio_list[1]
    if any("audio" in stream.mime_type for stream in list_item_yt_video):
        list_video_audio_resolution.append("mp3")
    return list_video_audio_resolution, lien_video

def default_path(*args):
    pathvar.set(
        path.join(DOWNLOAD_PATH, "audio")
        if "mp3" in option_video.get()
        else path.join(DOWNLOAD_PATH, "video")
    )

def check_path():
    pathvar.set(filedialog.askdirectory())

def download():
    def analyse_type(value):
        for resolution in list_form_video:
            if resolution in value:
                return resolution, "mp4" if "mp4" in value else "webm"
        return None, "mp3"

    type_download, video_type = analyse_type(option_video.get())
    try:
        if type_download is not None:
            video_content = lien_video.streams.filter(res=type_download, file_extension=video_type).first()
            video_content.download(pathvar.get())
            rename(
                path.join(pathvar.get(), f"{lien_video.title}.{video_type}"),
                path.join(pathvar.get(), f"{lien_video.title} - {type_download}.{video_type}"),
            )
        else:
            old_name = lien_video.streams.filter(only_audio=True).first().download(pathvar.get())
            new_name = path.splitext(old_name)
            rename(old_name, new_name[0] + ".mp3")
            remove(path.join(DOWNLOAD_PATH, "audio", f"{lien_video.title}.mp4"))
    except Exception as error:
        print(f"Error : {error}")
        CTkMessagebox(
            title="Error in download",
            icon="cancel",
            message="Problem in download!\nOr problem in path",
            text_color="red",
            font=text_style,
        )

def text_link(*args):
    try:
        global frame2_maked, Frame2
        if frame2_maked:
            Frame2.destroy()
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+-8+0")
        result_video_list, lien_video = value_dropdown_list()
        print(result_video_list, lien_video,1)
        Frame2 = CTkFrame(root, fg_color="#f0f0f0")
        Frame2.pack(expand=True, fill="both", side="bottom")
        
        option_video.set(result_video_list[0])
        path_img = path.join(IMAGE_DOWNLOAD_PATH, f"{get_title_video(lien_video)}.jpg")
        with open(path_img, "wb") as make_img:
            make_img.write(get_url(lien_video.thumbnail_url).content)

        label_title_video = CTkLabel(
            Frame2,
            text=(
                lien_video.title
                if len(lien_video.title) < 43
                else lien_video.title[:42] + "..."
            ),
            font=("Helvertica", 30, "bold"),
        )
        text_time_video_yt = CTkLabel(
            Frame2, text=calc_time(int(lien_video.length)), font=("Helvertica", 45, "bold")
        )
        zone_img_video = CTkLabel(
            Frame2,
            text="",
            image=CTkImage(
                dark_image=Image.open(path_img), size=(500, 325)
            ),
        )
        dropdown_menu_video_types = CTkOptionMenu(
            Frame2,
            variable=option_video,
            values=result_video_list,
            height=50,
            width=200,
            font=text_style,
            dropdown_hover_color="blue",
            dropdown_font=("Arial", 15),
            dropdown_text_color="#fff",
            dropdown_fg_color="black",
        )
        btn2_download = CTkButton(
            Frame2, text="Download", height=50, width=200, font=text_style, command=download
        )
        zone_text_path = CTkEntry(
            Frame2,
            textvariable=pathvar,
            height=50,
            width=550,
            font=("Helvertica", 17, "bold"),
        )
        btn3_choice_path = CTkButton(
            Frame2,
            text="Browse...",
            height=50,
            width=200,
            font=text_style,
            command=check_path,
        )
        remove(path_img)
        zone_img_video.place(x=50, y=10)
        label_title_video.place(x=560, y=25)
        text_time_video_yt.place(x=560, y=70)
        dropdown_menu_video_types.place(x=925, y=225)
        btn2_download.place(x=1135, y=225)
        zone_text_path.place(x=575, y=160)
        btn3_choice_path.place(x=1135, y=160)
        frame2_maked = True
    except Exception as error:
        CTkMessagebox(
            title="Error in link",
            icon="cancel",
            message="Problem in link!\nOr problem in connection",
            text_color="red",
            font=text_style,
        )

root = CTk()
root.geometry(f"800x375+{(root.winfo_screenwidth()-800)//2}+{(root.winfo_screenheight()-375)//2}")
list_form_video = ["4320p", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
video_extension = ["mp4", "webm"]
pathvar = StringVar()
entryvar = StringVar()
frame2_maked = False
text_style = ("Helvertica", 20, "bold")
option_video = StringVar()
option_video.trace("w", default_path)
path_logo_yt = CTkImage(
    dark_image=Image.open(
        path.join(IMAGE_DOWNLOAD_PATH, "YT-LOGO.png")
    ),
    size=(300, 150),
)
Frame1 = CTkFrame(root, fg_color="#f0f0f0")
Frame1.pack(side="top", fill="x", expand=False)
L_link_img_yt = CTkButton(
    Frame1,
    text="",
    fg_color="#f1f1f1",
    hover_color="#f0f0f0",
    image=path_logo_yt,
    border_width=0,
    command=link_yt,
    cursor="hand2",
)
L_title = CTkLabel(
    Frame1, text="Youtube video downloader", font=text_style, cursor="xterm"
)
input_link = CTkEntry(
    Frame1,
    placeholder_text="Write your YouTube video link ....",
    textvariable=entryvar,
    width=600,
    height=50,
    font=text_style,
    corner_radius=20,
)
btn_download = CTkButton(
    Frame1, text="Download", height=50, width=200, font=text_style, command=text_link
)
L_link_img_yt.pack(pady=20)
L_title.pack(pady=10)
input_link.pack()
btn_download.pack(pady=10)
root.config(background="#f0f0f0")
root.mainloop()
