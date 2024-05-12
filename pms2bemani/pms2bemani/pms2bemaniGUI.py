import tkinter
from tkinter import *
import json
import os
import jaconv
import subprocess
import re
import cutlet
from tkinter import filedialog as fd
from tkinter import messagebox
from tkinter.messagebox import showinfo,askyesno
from PIL import  ImageTk,ImageDraw,Image

class Application(tkinter.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_file = ''
        #load translation
        translation_file = open('gui_assets/gui_translation.json')
        translation_data = json.load(translation_file)
        self.tr = translation_data["languages"][translation_data["selected"]]
        translation_file.close()
        #style
        parent.title("Pms2bemani")
        parent.protocol("WM_DELETE_WINDOW",lambda: self.delete_window(parent))
        # Setting icon
        logo_img = PhotoImage(file ='gui_assets/logo.png')
        parent.iconphoto(False, logo_img)
        #load category data
        self.l = self.chara_txt_to_data()

        #grids
        for i in range(38):
          parent.columnconfigure(i, weight=10)
 
        #load masks
        mask_file = open('gui_assets/metadata.json')
        metadata = json.load(mask_file)
        mask_data = metadata["mask"]
        category_data = metadata["category"]
        mask_file.close()
        #masks array 
        #get texts
        self.mask_des = []
        self.mask_value = []
        for key in mask_data:
            self.mask_des.append(mask_data[key]["text"])
            self.mask_value.append(mask_data[key]["value"])
        self.vars_mask = []
        for label, value in zip(self.mask_des, self.mask_value):
            var = tkinter.IntVar(value=0)
            self.vars_mask.append(var)
        #category array 
        #get texts
        self.category_des = []
        self.category_value = []
        for key in category_data:
            self.category_des.append(category_data[key]["text"])
            self.category_value.append(category_data[key]["value"])
        self.vars_category = []
        for label, value in zip(self.category_des, self.category_value):
            var = tkinter.IntVar(value=0)
            self.vars_category.append(var)

        #check buttons vars
        self.has_battle_var = BooleanVar()
        self.is_jacket_var = BooleanVar()
        self.new_chart_format = BooleanVar()
        self.hariai_in_game = BooleanVar()
        # first menu
        self.menu_bar= tkinter.Menu(parent)
        self.menu_file = tkinter.Menu(self.menu_bar, tearoff=False)
        self.menu_file.add_command(label="New",command=lambda:self.new_fields(parent))
        self.menu_file.add_command(label="Open",command=lambda:self.open_p2b(parent))
        self.menu_file.add_command(label="Save",command=lambda:self.save())
        self.menu_file.add_command(label="Save As..",command=lambda:self.save_as(parent))
        self.menu_file.entryconfig(2, state=DISABLED)
        # Add options to menu.
        self.menu_bar.add_cascade(menu=self.menu_file, label=self.tr["File"])
        self.menu_bar.add_cascade(label=self.tr["Options"],command=lambda:self.options(parent))
        parent.config(menu=self.menu_bar)
        #create window widgets
        self.create_widgets(parent)


    def create_widgets(self,parent):
        #Mod data
        self.tag_mod_data = tkinter.Label(parent, text=self.tr["Mod data"])
        self.tag_mod_data.grid(column=0, row=0,pady = 2,sticky='ew')
        #Name
        self.tag_name = tkinter.Label(parent, text=self.tr["Name"])
        self.tag_name.grid(column=0, row=1,sticky="W",pady = 2)
        self.box_name = tkinter.Entry(parent)
        self.box_name.grid(column=1, row=1,sticky='ew')
        #Music ID
        vcmd = (self.register(self.callback))
        self.tag_music_id = tkinter.Label(parent, text=self.tr["Music ID"])
        self.tag_music_id.grid(column=0, row=2,sticky="W",pady = 2)
        self.box_music_id = tkinter.Entry(parent, validate='all', validatecommand=(vcmd, '%P'))
        self.box_music_id.grid(column=1, row=2,sticky='ew')
        #Keysounds folder
        self.tag_keysounds = tkinter.Label(parent, text=self.tr["Keysounds folder"])
        self.tag_keysounds.grid(column=0, row=3,sticky="W",pady = 2)
        self.box_keysounds = tkinter.Entry(parent)
        self.box_keysounds.grid(column=1, row=3,sticky='ew')
        self.find_keysounds = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_directory(self.box_keysounds))
        self.find_keysounds.grid(column=2, row=3,sticky="W")

 
        # Create the list of pop'n music levels
        self.levels = []
        [self.levels.append(x+1) for x in range(50)]
        # Variable to keep track of the option
        # selected in OptionMenu
        self.value_inside_bp_lv = tkinter.StringVar(parent)
        self.value_inside_ep_lv = tkinter.StringVar(parent)
        self.value_inside_np_lv = tkinter.StringVar(parent)
        self.value_inside_hp_lv = tkinter.StringVar(parent)
        self.value_inside_op_lv = tkinter.StringVar(parent)
        # Set the default value of the variable
        self.value_inside_bp_lv.set("1")
        self.value_inside_ep_lv.set("1")
        self.value_inside_np_lv.set("1")
        self.value_inside_hp_lv.set("1")
        self.value_inside_op_lv.set("1")


        #Charts title
        self.tag_charts_title = tkinter.Label(parent, text=self.tr["Charts"])
        self.tag_charts_title.grid(column=0, row=5,pady = 2,sticky='ew')
        self.tag_charts_title = tkinter.Label(parent, text=self.tr["Level"])
        self.tag_charts_title.grid(column=3, row=5,pady = 2,sticky='ew')
        #battle mode stuff
        self.tag_input_bp = tkinter.Label(parent, text=self.tr["Battle Mode File"])
        self.tag_input_bp.grid(column=0, row=6,sticky="W",pady = 2)
        self.box_input_bp = tkinter.Entry(parent)
        self.box_input_bp.grid(column=1, row=6,sticky='ew')
        self.find_input_bp = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_pms(self.box_input_bp))
        self.find_input_bp.grid(column=2, row=6,sticky="W")
        #battle mode level objects
        self.question_menu_bp_lv = tkinter.OptionMenu(parent, self.value_inside_bp_lv, *self.levels)
        self.question_menu_bp_lv.grid(column=3, row=6,sticky="EW")
        #Easy difficulty
        self.tag_input_ep = tkinter.Label(parent, text=self.tr["Easy Chart File"])
        self.tag_input_ep.grid(column=0, row=7,sticky="W",pady = 2)
        self.box_input_ep = tkinter.Entry(parent)
        self.box_input_ep.grid(column=1, row=7,sticky='ew')
        self.find_input_ep = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_pms(self.box_input_ep))
        self.find_input_ep.grid(column=2, row=7,sticky="W")        
        #Easy difficulty level objects
        self.question_menu_ep_lv = tkinter.OptionMenu(parent, self.value_inside_ep_lv, *self.levels)
        self.question_menu_ep_lv.grid(column=3, row=7,sticky="EW")
        #Normal difficulty
        self.tag_input_np = tkinter.Label(parent, text=self.tr["Normal Chart File"])
        self.tag_input_np.grid(column=0, row=8,sticky="W",pady = 2)
        self.box_input_np = tkinter.Entry(parent)
        self.box_input_np.grid(column=1, row=8,sticky='ew')
        self.find_input_np = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_pms(self.box_input_np))
        self.find_input_np.grid(column=2, row=8,sticky="W")
        #Normal difficulty level objects
        self.question_menu_np_lv = tkinter.OptionMenu(parent, self.value_inside_np_lv, *self.levels)
        self.question_menu_np_lv.grid(column=3, row=8,sticky="EW")
        #Hyper difficulty
        self.tag_input_hp = tkinter.Label(parent, text=self.tr["Hyper Chart File"])
        self.tag_input_hp.grid(column=0, row=9,sticky="W",pady = 2)
        self.box_input_hp = tkinter.Entry(parent)
        self.box_input_hp.grid(column=1, row=9,sticky='ew')
        self.find_input_hp = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_pms(self.box_input_hp))
        self.find_input_hp.grid(column=2, row=9,sticky="W")
        #Hyper difficulty level objects
        self.question_menu_hp_lv = tkinter.OptionMenu(parent, self.value_inside_hp_lv, *self.levels)
        self.question_menu_hp_lv.grid(column=3, row=9,sticky="EW")
        #Ex difficulty
        self.tag_input_op = tkinter.Label(parent, text=self.tr["Ex Chart File"])
        self.tag_input_op.grid(column=0, row=10,sticky="W",pady = 2)
        self.box_input_op = tkinter.Entry(parent)
        self.box_input_op.grid(column=1, row=10,sticky='ew')
        self.find_input_op = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_pms(self.box_input_op))
        self.find_input_op.grid(column=2, row=10,sticky="W")
        #Ex difficulty level objects
        self.question_menu_op_lv = tkinter.OptionMenu(parent, self.value_inside_op_lv, *self.levels)
        self.question_menu_op_lv.grid(column=3, row=10,sticky="EW")
        #Metadata
        self.tag_metadata = tkinter.Label(parent, text=self.tr["Metadata"])
        self.tag_metadata.grid(column=0, row=11,pady = 2,sticky='ew')
        #FW title
        self.tag_fw_title = tkinter.Label(parent, text=self.tr["FW title"])
        self.tag_fw_title.grid(column=0, row=12,sticky="W",pady = 2)
        self.box_fw_title = tkinter.Entry(parent)
        self.box_fw_title.grid(column=1, row=12,sticky='ew')
        self.btn_fw_title = tkinter.Button(parent,text=self.tr["FW"],command=lambda: self.half2full(self.box_fw_title,self.box_fw_title ))
        self.btn_fw_title.grid(column=2, row=12,sticky="W")
        #FW artist
        self.tag_fw_artist = tkinter.Label(parent, text=self.tr["FW artist"])
        self.tag_fw_artist.grid(column=0, row=13,sticky="W",pady = 2)
        self.box_fw_artist = tkinter.Entry(parent)
        self.box_fw_artist.grid(column=1, row=13,sticky='ew')
        self.btn_fw_artist = tkinter.Button(parent,text=self.tr["FW"],command=lambda: self.half2full(self.box_fw_artist,self.box_fw_artist ))
        self.btn_fw_artist.grid(column=2, row=13,sticky="W")
        #FW genre
        self.tag_fw_genre = tkinter.Label(parent, text=self.tr["FW genre"])
        self.tag_fw_genre.grid(column=0, row=14,sticky="W",pady = 2)
        self.box_fw_genre = tkinter.Entry(parent)
        self.box_fw_genre.grid(column=1, row=14,sticky='ew')
        self.btn_fw_genre = tkinter.Button(parent,text=self.tr["FW"],command=lambda: self.half2full(self.box_fw_genre,self.box_fw_genre ))
        self.btn_fw_genre.grid(column=2, row=14,sticky="W")
        #Title
        self.tag_title = tkinter.Label(parent, text=self.tr["Title"])
        self.tag_title.grid(column=0, row=15,sticky="W",pady = 2)
        self.box_title = tkinter.Entry(parent)
        self.box_title.grid(column=1, row=15,sticky='ew')
        #Artist
        self.tag_artist = tkinter.Label(parent, text=self.tr["Artist"])
        self.tag_artist.grid(column=0, row=16,sticky="W",pady = 2)
        self.box_artist = tkinter.Entry(parent)
        self.box_artist.grid(column=1, row=16,sticky='ew')
        #Genre
        self.tag_genre = tkinter.Label(parent, text=self.tr["Genre"])
        self.tag_genre.grid(column=0, row=17,sticky="W",pady = 2)
        self.box_genre = tkinter.Entry(parent)
        self.box_genre.grid(column=1, row=17,sticky='ew')
        #Chara 1
        self.tag_chara_1 = tkinter.Label(parent, text=self.tr["Chara 1"])
        self.tag_chara_1.grid(column=0, row=18,sticky="W",pady = 2)
        self.box_chara_1 = tkinter.Entry(parent)
        self.box_chara_1.grid(column=1, row=18,sticky='ew')
        self.sel_chara_1 = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.chara_selection(parent,self.box_chara_1,0))
        self.sel_chara_1.grid(column=2, row=18,sticky="W")
        #Chara 2
        self.tag_chara_2 = tkinter.Label(parent, text=self.tr["Chara 2"])
        self.tag_chara_2.grid(column=0, row=19,sticky="W",pady = 2)
        self.box_chara_2 = tkinter.Entry(parent)
        self.box_chara_2.grid(column=1, row=19,sticky='ew')
        self.sel_chara_2 = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.chara_selection(parent,self.box_chara_2,0))
        self.sel_chara_2.grid(column=2, row=19,sticky="W")
        #Has battle hyper
        self.tag_battle_hyper = tkinter.Label(parent, text=self.tr["Has battle hyper"])
        self.tag_battle_hyper.grid(column=0, row=20,sticky="W",pady = 2)
        self.check_battle_hyper = tkinter.Checkbutton(parent,onvalue=True, offvalue=False,variable=self.has_battle_var)
        self.check_battle_hyper.grid(column=1, row=20,sticky="W",pady = 2)
        #Hariai is jacket
        self.tag_is_jacket = tkinter.Label(parent, text=self.tr["Hariai is jacket"])
        self.tag_is_jacket.grid(column=0, row=21,sticky="W",pady = 2)
        self.check_is_jacket = tkinter.Checkbutton(parent,onvalue=True, offvalue=False,variable=self.is_jacket_var)
        self.check_is_jacket.grid(column=1, row=21,sticky="W",pady = 2)

        #Folder (version)
        self.tag_version = tkinter.Label(parent, text=self.tr["Folder"])
        self.tag_version.grid(column=0, row=22,sticky="W",pady = 2)
        # Create the list of pop'n music versions
        self.versions = []
        [self.versions.append(x+1) for x in range(27)]
        # Variable to keep track of the option
        # selected in OptionMenu
        self.value_inside_folder = tkinter.StringVar(parent)
        # Set the default value of the variable
        self.value_inside_folder.set(None)
        # Create the option menu widget and passing 
        # the options_list and value_inside to it.
        self.question_menu_folder = tkinter.OptionMenu(parent, self.value_inside_folder, *self.versions)
        self.question_menu_folder.grid(column=1, row=22,sticky="EW")
        #clean options
        self.clean_folder = tkinter.Button(parent,text=self.tr["Clean"],command=lambda: self.clean_value(self.value_inside_folder))
        self.clean_folder.grid(column=2, row=22,sticky="W")

        #Category
        self.tag_category = tkinter.Label(parent, text=self.tr["Categories"])
        self.tag_category.grid(column=0, row=23,sticky="W",pady = 2)
        self.create_category = tkinter.Button(parent,text=self.tr["Open"],command=lambda:self.optionWindow(parent,self.category_des,self.category_value,self.vars_category,self.tr["Categories"]))
        self.create_category.grid(column=1, row=23,sticky="W",pady = 2)


        #CS Version
        self.tag_cs = tkinter.Label(parent, text=self.tr["CS Version"])
        self.tag_cs.grid(column=0, row=24,sticky="W",pady = 2)
        #Category list menu
        # Variable to keep track of the option
        # selected in OptionMenu
        self.value_inside_cs = tkinter.StringVar(parent)
        # Set the default value of the variable
        self.value_inside_cs.set(None)
        # Create the option menu widget and passing 
        # the options_list and value_inside to it.
        self.cs_versions = []
        [self.cs_versions.append(x+1) for x in range(1)]
        self.question_menu_cs = tkinter.OptionMenu(parent, self.value_inside_cs, *self.cs_versions)
        self.question_menu_cs.grid(column=1, row=24,sticky="EW")
        #clean options
        self.clean_cs = tkinter.Button(parent,text=self.tr["Clean"],command=lambda: self.clean_value(self.value_inside_cs))
        self.clean_cs.grid(column=2, row=24,sticky="W")

        #Mask
        self.tag_mask = tkinter.Label(parent, text=self.tr["Mask"])
        self.tag_mask.grid(column=0, row=25,sticky="W",pady = 2)
        #Mask subwindow
        self.create_mask = tkinter.Button(parent,text=self.tr["Open"],command=lambda:self.optionWindow(parent,self.mask_des,self.mask_value,self.vars_mask,self.tr["Mask"]))
        self.create_mask.grid(column=1, row=25,sticky="W",pady = 2)


        #Chara X
        self.tag_chara_position_x = tkinter.Label(parent, text=self.tr["Chara position X"])
        self.tag_chara_position_x.grid(column=0, row=26,sticky="W",pady = 2)
        self.box_chara_position_x = tkinter.Spinbox(from_=0,to=2000,increment=1,validate='all', validatecommand=(vcmd, '%P'))
        self.box_chara_position_x.grid(column=1, row=26)
        #Chara Y
        self.tag_chara_position_y = tkinter.Label(parent, text=self.tr["Chara position Y"])
        self.tag_chara_position_y.grid(column=0, row=27,sticky="W",pady = 2)
        self.box_chara_position_y = tkinter.Spinbox(from_=0,to=2000,increment=1,validate='all', validatecommand=(vcmd, '%P'))
        self.box_chara_position_y.grid(column=1, row=27)

        #Preview
        self.tag_preview = tkinter.Label(parent, text=self.tr["Preview"])
        self.tag_preview.grid(column=0, row=28,pady = 2,sticky='ew')

        #Preview File
        self.tag_preview_file = tkinter.Label(parent, text=self.tr["Preview file"])
        self.tag_preview_file.grid(column=0, row=29,sticky="W",pady = 2)
        self.box_preview_file = tkinter.Entry(parent)
        self.box_preview_file.grid(column=1, row=29,sticky='ew')
        self.find_preview_file = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_sound(self.box_preview_file))
        self.find_preview_file.grid(column=2, row=29,sticky="W")

        #Preview offset
        self.tag_preview_offset = tkinter.Label(parent, text=self.tr["Preview offset"])
        self.tag_preview_offset.grid(column=0, row=30,sticky="W",pady = 2)
        self.box_preview_offset = tkinter.Spinbox(from_=0,to=2000,increment=1,validate='all', validatecommand=(vcmd, '%P'))
        self.box_preview_offset.grid(column=1, row=30)

        #Preview duration
        self.tag_preview_duration = tkinter.Label(parent, text=self.tr["Preview duration"])
        self.tag_preview_duration.grid(column=0, row=31,sticky="W",pady = 2)
        self.box_preview_duration = tkinter.Spinbox(from_=0,to=2000,increment=1,validate='all', validatecommand=(vcmd, '%P'))
        self.box_preview_duration.grid(column=1, row=31)

        #Extra
        self.tag_extra = tkinter.Label(parent, text=self.tr["Extra"])
        self.tag_extra.grid(column=5, row=21,pady = 2,sticky='ew')

        #New chart format
        self.tag_new_format = tkinter.Label(parent, text=self.tr["New chart format"])
        self.tag_new_format.grid(column=5, row=22,sticky="W",pady = 2)
        self.check_new_format = tkinter.Checkbutton(parent,onvalue=True, offvalue=False,variable=self.new_chart_format)
        self.check_new_format.grid(column=6, row=22,sticky="W",pady = 2)

        #Banner
        self.tag_banner = tkinter.Label(parent, text=self.tr["Banner"])
        self.tag_banner.grid(column=5, row=23,sticky="W",pady = 2)
        self.box_banner = tkinter.Entry(parent)
        self.box_banner.grid(column=6, row=23,sticky='ew')
        self.find_banner = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_image(self.box_banner,parent,"banner"))
        self.find_banner.grid(column=7, row=23,sticky="W")
        self.clean_banner = tkinter.Button(parent,text=self.tr["Clean"],command=lambda: self.clean_image(parent,"banner",self.box_banner))
        self.clean_banner.grid(column=8, row=23,sticky="w",columnspan=1)

        #Background
        empty = tkinter.Label(parent)
        empty.grid(column=4, row=22,sticky="W")
        self.tag_background = tkinter.Label(parent, text=self.tr["Background"])
        self.tag_background.grid(column=5, row=24,sticky="W",pady = 2)
        self.box_background = tkinter.Entry(parent)
        self.box_background.grid(column=6, row=24,sticky='ew')
        self.find_background = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_image(self.box_background,parent,"bg"))
        self.find_background.grid(column=7, row=24,sticky="W")
        self.clean_background = tkinter.Button(parent,text=self.tr["Clean"],command=lambda: self.clean_image(parent,"bg",self.box_background))
        self.clean_background.grid(column=8, row=24,sticky="w")

        #Hariai
        self.tag_hariai = tkinter.Label(parent, text=self.tr["Hariai"])
        self.tag_hariai.grid(column=5, row=25,sticky="W",pady = 2)
        self.box_hariai = tkinter.Entry(parent)
        self.box_hariai.grid(column=6, row=25,sticky='ew')
        self.find_hariai = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_file_image(self.box_hariai,parent,"hariai"))
        self.find_hariai.grid(column=7, row=25,sticky="W")
        self.clean_hariai = tkinter.Button(parent,text=self.tr["Clean"],command=lambda: self.clean_image(parent,"hariai",self.box_hariai))
        self.clean_hariai.grid(column=8, row=25,sticky="w",columnspan=1)
        #Hariai from game
        self.tag_game_hariai = tkinter.Label(parent, text=self.tr["From game files"])
        self.tag_game_hariai.grid(column=5, row=26,sticky="W",pady = 2)
        self.check_game_hariai = tkinter.Checkbutton(parent,onvalue=True, offvalue=False,variable=self.hariai_in_game)
        self.check_game_hariai.grid(column=6, row=26,sticky='ew')
        self.game_hariai = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.chara_selection(parent,self.box_hariai,2))
        self.game_hariai.grid(column=7, row=26,sticky="w",columnspan=1)
 


        #Output folder
        self.tag_output = tkinter.Label(parent, text=self.tr["Output folder"])
        self.tag_output.grid(column=5, row=27,sticky="W",pady = 2)
        self.box_output= tkinter.Entry(parent)
        self.box_output.grid(column=6, row=27,sticky='ew')
        self.find_output = tkinter.Button(parent,text=self.tr["Open"],command=lambda: self.select_directory(self.box_output))
        self.find_output.grid(column=7, row=27,sticky="W")

        #Create Mod
        self.create_mod = tkinter.Button(parent,text=self.tr["Create Mod"],command=lambda:self.generate_mod())
        self.create_mod.grid(column=6, row=29,sticky="EW")

        #Banner display
        self.tag_image_banner=tkinter.Label(parent, text=self.tr["Banner"])
        self.tag_image_banner.grid(column=6, row=0,sticky="E",pady = 2)
        self.clean_image(parent,"banner",self.box_banner)

        #Bg display
        self.tag_image_bg=tkinter.Label(parent, text=self.tr["Background"])
        self.tag_image_bg.grid(column=7, row=4,sticky="EW",pady = 10)
        self.clean_image(parent,"bg",self.box_background)


        #Hariai display
        self.tag_image_hariai = tkinter.Label(parent, text=self.tr["Hariai"])
        self.tag_image_hariai.grid(column=6, row=4,sticky="W",pady = 3)
        self.clean_image(parent,"hariai",self.box_hariai)


    def box_to_param(self,param,widget):
        if ((widget.get() != '') and (widget.get() != 'None')):
            self.params.append(param)
            self.params.append(widget.get())

    def num_box_to_param(self,param,widget):
        if ((widget.get() != '') and (widget.get() != '0')):
            self.params.append(param)
            self.params.append(widget.get())

    def bool_to_param(self,param,widget):
        if widget.get():
            self.params.append(param)

    def bitfields_to_param(self,param,variables):
        values = [var.get() for var in variables]
        result = sum(values)
        if result > 0:
            self.params.append(param)
            self.params.append(str(result))
          #get data for our file

    def generate_mod(self):
      self.params = []
      #get config stuff for our command
      options = self.load_config_file()
      if options["command"] != '':
           self.params.append(options["command"])
      else:
           self.params.append("python")

      self.params.append('pms2bemani.py')
      #Create command based on our fields
      self.box_to_param("--name",self.box_name)
      self.box_to_param("--musicid",self.box_music_id)
      self.box_to_param("--keysounds-folder",self.box_keysounds)
      self.box_to_param("--banner",self.box_banner)
      self.box_to_param("--input-bp",self.box_input_bp)
      self.box_to_param("--input-ep",self.box_input_ep)
      self.box_to_param("--input-np",self.box_input_np)
      self.box_to_param("--input-hp",self.box_input_hp)
      self.box_to_param("--input-op",self.box_input_op)
      self.box_to_param("--metadata-fw-title",self.box_fw_title)
      self.box_to_param("--metadata-fw-artist",self.box_fw_artist)
      self.box_to_param("--metadata-fw-genre",self.box_fw_genre)
      self.box_to_param("--metadata-title",self.box_title)
      self.box_to_param("--metadata-artist",self.box_artist)
      self.box_to_param("--metadata-genre",self.box_genre)
      self.box_to_param("--metadata-chara1",self.box_chara_1)
      self.box_to_param("--metadata-chara2",self.box_chara_2)
      self.bool_to_param("--metadata-has-battle-hyper",self.has_battle_var)
      self.bool_to_param("--metadata-hariai-is-jacket",self.is_jacket_var)
      self.bool_to_param("--metadata-hariai-in-game",self.hariai_in_game)
      self.box_to_param("--metadata-folder",self.value_inside_folder)
      self.box_to_param("--lvl-bp",self.value_inside_bp_lv)
      self.box_to_param("--lvl-ep",self.value_inside_ep_lv)
      self.box_to_param("--lvl-np",self.value_inside_np_lv)
      self.box_to_param("--lvl-hp",self.value_inside_hp_lv)
      self.box_to_param("--lvl-op",self.value_inside_op_lv)
      self.bitfields_to_param("--metadata-categories",self.vars_category)
      self.box_to_param("--metadata-cs-version",self.value_inside_cs)
      self.bitfields_to_param("--metadata-mask",self.vars_mask)
      self.num_box_to_param("--metadata-chara-x",self.box_chara_position_x)
      self.num_box_to_param("--metadata-chara-y",self.box_chara_position_y)
      self.box_to_param("--preview",self.box_preview_file)
      self.num_box_to_param("--preview-offset",self.box_preview_offset)
      self.num_box_to_param("--preview-duration",self.box_preview_duration)
      self.bool_to_param("--new",self.new_chart_format)
      self.box_to_param("--bg",self.box_background)
      self.box_to_param("--hariai",self.box_hariai)
      self.box_to_param("--output",self.box_output)
      subprocess.call(self.params)
      print("==========PROCESS COMPLETED==========")

    #Function that create subwindows for bitfield forms
    def optionWindow(self,parent,descriptions,values,array,title):
        
        # Toplevel object which will
        # be treated as a new window
        ctWin = Toplevel(parent)
        # sets the title of the
        # Toplevel widget
        ctWin.title(title)  
        # sets the geometry of toplevel
        ctWin.geometry("400x400")
        for i in range(14):
          ctWin.columnconfigure(i, weight=3)
        #generate check buttons
        count = 0
        for label, value in zip(descriptions, values):
            cb = tkinter.Checkbutton(ctWin, text=label, onvalue=value, offvalue=0, variable=array[count])
            cb.grid(column=0, row=count,sticky="W")
            cb.var = array[count]
            count  = count + 1

        ctWin.transient(parent)
        ctWin.grab_set()
        parent.wait_window(ctWin)
        
    #validations
    #validate int entrys
    def callback(self, P):
        if str.isdigit(P) or P == "":
            return True
        else:
            return False

    def select_directory(self,widget):
        folder = fd.askdirectory()
        if folder == '': 
          return
        widget.delete(0,"end")
        widget.insert(0,folder)

    def select_file_image(self,widget,parent,type):
        filetypes = (
            ('PNG file', '*.png'),
            ('All files', '*.*')
        )
        filename = fd.askopenfilename(
            title='Open a file',
            #save folder
            initialdir = "/áéá",
            filetypes=filetypes)
        #validate is a png
        if filename == '': 
          return
        if filename.endswith('.png'):
         self.insert_image(parent,filename,widget,type)


    def insert_image(self,parent,filename,widget,type):
         my_image=Image.open(filename)
         banner = ImageTk.PhotoImage(my_image)
 
         if type == "banner" and my_image.size == (244,58):
          self.tag_image_banner = tkinter.Label(parent,image=banner)
          self.tag_image_banner.image = banner
          self.tag_image_banner.grid(column=6, row=0,sticky="W",pady = 2,rowspan=4,columnspan=3)
         elif type == "bg" and my_image.size == (128, 256):
          self.tag_image_bg = tkinter.Label(parent,image=banner)
          self.tag_image_bg.image = banner
          self.tag_image_bg.grid(column=7, row=4,sticky="W",pady = 2,rowspan=13,columnspan=2)
         elif type == "hariai" and ((my_image.size == (250, 322)) or (my_image.size == (382, 502))):
            if((my_image.size == (382, 502))):
              my_image = my_image.resize((250, 322))
            banner = ImageTk.PhotoImage(my_image)
            self.tag_image_hariai = tkinter.Label(parent,image=banner)
            self.tag_image_hariai.image = banner
            self.tag_image_hariai.grid(column=4, row=5,sticky="W",pady = 2,rowspan=13,columnspan=3)
            self.hariai_in_game.set(False)
         else:
            tkinter.messagebox.showerror(title="Error", message=self.tr["Image error"])
            return 0
         widget.delete(0,"end")
         widget.insert(0,filename)

    
         
    def clean_image(self,parent,type,widget):
        if type == "bg":
         image=Image.open('gui_assets/bg.png')
         image_ui = ImageTk.PhotoImage(image)
         self.tag_image_bg = tkinter.Label(parent,image=image_ui)
         self.tag_image_bg.image = image_ui
         self.tag_image_bg.grid(column=7, row=4,sticky="W",pady = 2,rowspan=13,columnspan=2)
         widget.delete(0,"end")
        elif type == "banner":
         image=Image.open('gui_assets/banner.png')
         image_ui = ImageTk.PhotoImage(image)
         self.tag_image_banner=tkinter.Label(parent,image=image_ui)
         self.tag_image_banner.image = image_ui
         self.tag_image_banner.grid(column=6, row=0,sticky="W",pady = 2,rowspan=4,columnspan=3)
         widget.delete(0,"end")
        elif type == "hariai":
         image=Image.open('gui_assets/hariai.png')
         image_ui = ImageTk.PhotoImage(image)
         self.tag_image_hariai=tkinter.Label(parent,image=image_ui)
         self.tag_image_hariai.image = image_ui
         self.tag_image_hariai.grid(column=4, row=5,sticky="W",pady = 2,rowspan=13,columnspan=3)
         widget.delete(0,"end")

    def select_file_pms(self,widget):
        filetypes = (
            ('Pms files', '*.pms'),
            ('All files', '*.*')
        )
        filename = fd.askopenfilename(
            title='Open a file',
            #save folder
            initialdir = "/áéá",
            filetypes=filetypes)
        if filename == '': 
          return
        widget.delete(0,"end")
        widget.insert(0,filename)

    def select_file_sound(self,widget):
        filetypes = (
            ('OGG', '*.ogg'),
            ('Waveform Audio Format', '*.wav'),
            ('All files', '*.*')
        )
        filename = fd.askopenfilename(
            title='Open a file',
            #save folder
            initialdir = "/áéá",
            filetypes=filetypes)
        if filename == '': 
          return
        widget.delete(0,"end")
        widget.insert(0,filename)

    def clean_value(self,widget):
        widget.set(None)

    def change_language(self,language):
         translation_file = open('gui_assets/gui_translation.json')
         translation_data = json.load(translation_file)
         self.tr = translation_data["languages"][language]
         self.tag_input_bp['text'] = self.tr["Battle Mode File"]
         translation_file.close()


    def half2full(self,widget,widget2):
         text = widget.get()
         #regex for FW fields
         if re.match("^[A-Za-zａ-ｚＡ-Ｚ０-９0-9゠-ヿ_ ?　!,.=*/／＊？！，．＝-]*$", widget.get()):
           widget2.delete(0,"end")
           widget2.insert(0,jaconv.h2z(text.upper(), kana=True, digit=True, ascii=True))
         else:
            tkinter.messagebox.showerror(title="Error", message=self.tr["Fw error"])


    def open_p2b(self,parent):
        filetypes = [('Pms2bemani Files', '*.p2b'),
                      ('All Files', '*.*')]
        filename = fd.askopenfilename(
            title='Open a file',
            #save folder
            initialdir = "/áéá",
            filetypes=filetypes)
        #check we select a file
        if filename == '': 
          return
        if filename.endswith('.p2b'):
          #load translation
          p2b_file = open(filename)
          p2b__data = json.load(p2b_file)
          parent.title(filename.split("/")[-1])
          self.current_file = filename
          self.p2b_to_fields(p2b__data,parent)


    def save_as(self,parent):
        files = [('Pms2bemani Files', '*.p2b'),
                      ('All Files', '*.*')]
        #get current file name
        file_now = ''
        if self.current_file != '':
         file_now=self.current_file.split("/")[-1]
        file = fd.asksaveasfile(filetypes = files, defaultextension = files,
         initialfile=file_now)
        if file is None: # asksaveasfile return `None` if dialog closed with "cancel".
         return
        file.write(self.fields_to_p2b())
        self.current_file = file.name
        parent.title(file.name.split("/")[-1])
        self.menu_file.entryconfig(2, state=ACTIVE)
        file.close() 

    def save(self):
        with open(self.current_file, 'w') as file:
         file.write(self.fields_to_p2b())
         file.close() 


    def fields_to_p2b(self):
      data = {}
      #get data for our file
      data["Name"]=self.box_name.get()
      data["Music ID"]=self.box_music_id.get()
      data["Keysounds folder"]=self.box_keysounds.get()
      data["Banner"]=self.box_banner.get()
      data["Battle Mode File"]=self.box_input_bp.get()
      data["Easy Chart File"]=self.box_input_ep.get()
      data["Normal Chart File"]=self.box_input_np.get()
      data["Hyper Chart File"]=self.box_input_hp.get()
      data["Ex Chart File"]=self.box_input_op.get()
      data["FW title"]=self.box_fw_title.get()
      data["FW artist"]=self.box_fw_artist.get()
      data["FW genre"]=self.box_fw_genre.get()
      data["Title"]=self.box_title.get()
      data["Artist"]=self.box_artist.get()
      data["Genre"]=self.box_genre.get()
      data["Chara 1"]=self.box_chara_1.get()
      data["Chara 2"]=self.box_chara_2.get()
      data["Has battle hyper"]=self.has_battle_var.get()
      data["Hariai is jacket"]=self.is_jacket_var.get()
      data["Folder"]=self.value_inside_folder.get()
      data["Lvl bp"]=self.value_inside_bp_lv.get()
      data["Lvl ep"]=self.value_inside_ep_lv.get()
      data["Lvl np"]=self.value_inside_np_lv.get()
      data["Lvl hp"]=self.value_inside_hp_lv.get()
      data["Lvl op"]=self.value_inside_op_lv.get()

      category_data = {}
      for label, value in zip(self.category_des, self.vars_category):
          category_data[label] = value.get()
      data["Categories"]=category_data

      data["CS Version"]=self.value_inside_cs.get()

      mask_data = {}
      for label, value in zip(self.mask_des, self.vars_mask):
          mask_data[label] = value.get()
      data["Mask"]=mask_data

      data["Chara position X"]=self.box_chara_position_x.get()
      data["Chara position Y"]=self.box_chara_position_y.get()
      data["Preview file"]=self.box_preview_file.get()
      data["Preview offset"]=self.box_preview_offset.get()
      data["Preview duration"]=self.box_preview_duration.get()
      data["New chart format"]=self.new_chart_format.get()
      data["Background"]=self.box_background.get()
      data["Hariai"]=self.box_hariai.get()
      data["Hariai in game"]=self.hariai_in_game.get()
      data["Output folder"]=self.box_output.get()

      return(json.dumps(data))
    

    def set_val(self, data, name: str, default: str = "") -> str:
        val = data.get(name)
        
        if val is None:
            return default
        if type(val)  != str:
            return default
        return val
    
    def set_bool(self, data, name: str, default: bool = False) -> bool:
        val = data.get(name)
        
        if val is None:
            return default
        if type(val)  != bool:
            return default
        return val


    def p2b_to_fields(self,data,parent):

      self.replace_value(self.box_name,data["Name"])
      self.replace_value(self.box_music_id,data["Music ID"])
      self.replace_value(self.box_keysounds,data["Keysounds folder"])
      self.replace_value(self.box_banner,data["Banner"])
      self.replace_value(self.box_input_bp,data["Battle Mode File"])
      self.replace_value(self.box_input_ep,data["Easy Chart File"])
      self.replace_value(self.box_input_np,data["Normal Chart File"])
      self.replace_value(self.box_input_hp,data["Hyper Chart File"])
      self.replace_value(self.box_input_op,data["Ex Chart File"])
      self.replace_value(self.box_fw_title,data["FW title"])
      self.replace_value(self.box_fw_artist,data["FW artist"])
      self.replace_value(self.box_fw_genre,data["FW genre"])
      self.replace_value(self.box_title,data["Title"])
      self.replace_value(self.box_artist,data["Artist"])
      self.replace_value(self.box_genre,data["Genre"])
      self.replace_value(self.box_chara_1,data["Chara 1"])
      self.replace_value(self.box_chara_2,data["Chara 2"])
      self.has_battle_var.set(data["Has battle hyper"])
      self.is_jacket_var.set(data["Hariai is jacket"])
      self.value_inside_folder.set(data["Folder"])
      self.value_inside_bp_lv.set(self.set_val(data,"Lvl bp","1"))
      self.value_inside_ep_lv.set(self.set_val(data,"Lvl ep","1"))
      self.value_inside_np_lv.set(self.set_val(data,"Lvl np","1"))
      self.value_inside_hp_lv.set(self.set_val(data,"Lvl hp","1"))
      self.value_inside_op_lv.set(self.set_val(data,"Lvl op","1"))
      
      for label, value in zip(self.category_des, self.vars_category):
          value.set(data["Categories"][label])

      self.value_inside_cs.set(data["CS Version"])


      for label, value in zip(self.mask_des, self.vars_mask):
          value.set(data["Mask"][label])

      self.replace_value(self.box_chara_position_x,data["Chara position X"])
      self.replace_value(self.box_chara_position_y,data["Chara position Y"])
      self.replace_value(self.box_preview_file,data["Preview file"])
      self.replace_value(self.box_preview_offset,data["Preview offset"])
      self.replace_value(self.box_preview_duration,data["Preview duration"])
      self.new_chart_format.set(data["New chart format"])
      self.replace_value(self.box_background,data["Background"])
      self.replace_value(self.box_hariai,data["Hariai"])
      self.replace_value(self.box_output,data["Output folder"])

      #clean images
      self.clean_image(parent,"bg",self.box_background)
      self.clean_image(parent,"banner",self.box_banner)
      self.clean_image(parent,"hariai",self.box_hariai)
      #insert images
      if(data["Banner"]!=''):
        self.insert_image(parent,data["Banner"],self.box_banner,"banner")
      if(data["Background"]!=''):
        self.insert_image(parent,data["Background"],self.box_background,"bg")

      hariai_is_in_game = self.set_bool(data,"Hariai in game")
      self.hariai_in_game.set(hariai_is_in_game)
      if(data["Hariai"]!=''):
        if hariai_is_in_game == False:
            self.insert_image(parent,data["Hariai"],self.box_hariai,"hariai")
        else:
            self.box_hariai.delete(0,"end")
            self.box_hariai.insert(0,data["Hariai"])


      self.menu_file.entryconfig(2, state=ACTIVE)

    def new_fields(self,parent):
      #clean all fields
      self.replace_value(self.box_name,"")
      self.replace_value(self.box_music_id,"")
      self.replace_value(self.box_keysounds,"")
      self.replace_value(self.box_banner,"")
      self.replace_value(self.box_input_bp,"")
      self.replace_value(self.box_input_ep,"")
      self.replace_value(self.box_input_np,"")
      self.replace_value(self.box_input_hp,"")
      self.replace_value(self.box_input_op,"")
      self.replace_value(self.box_fw_title,"")
      self.replace_value(self.box_fw_artist,"")
      self.replace_value(self.box_fw_genre,"")
      self.replace_value(self.box_title,"")
      self.replace_value(self.box_artist,"")
      self.replace_value(self.box_genre,"")
      self.replace_value(self.box_chara_1,"")
      self.replace_value(self.box_chara_2,"")
      self.has_battle_var.set(False)
      self.is_jacket_var.set(False)
      self.value_inside_folder.set(None)
      self.value_inside_bp_lv.set(1)
      self.value_inside_ep_lv.set(1)
      self.value_inside_np_lv.set(1)
      self.value_inside_hp_lv.set(1)
      self.value_inside_op_lv.set(1)
      
      for label, value in zip(self.category_des, self.vars_category):
          value.set(0)

      self.value_inside_cs.set(None)


      for label, value in zip(self.mask_des, self.vars_mask):
          value.set(0)

      self.replace_value(self.box_chara_position_x,0)
      self.replace_value(self.box_chara_position_y,0)
      self.replace_value(self.box_preview_file,"")
      self.replace_value(self.box_preview_offset,0)
      self.replace_value(self.box_preview_duration,0)
      self.new_chart_format.set(False)
      self.replace_value(self.box_background,"")
      self.replace_value(self.box_hariai,"")
      self.hariai_in_game.set(False)
      self.replace_value(self.box_output,"")

      #clean images
      self.clean_image(parent,"bg",self.box_background)
      self.clean_image(parent,"banner",self.box_banner)
      self.clean_image(parent,"hariai",self.box_hariai)
      self.current_file = ''
      self.menu_file.entryconfig(2, state=DISABLED)
      parent.title("Pms2bemani")


    def replace_value(self,widget,value):
        widget.delete(0,"end")
        widget.insert(0,value)


    def options(self,parent):
        # Toplevel object which will
        # be treated as a new window
        ctWin = Toplevel(parent)
        # sets the title of the
        # Toplevel widget
        ctWin.title(self.tr["Options"])  
        for i in range(4):
          ctWin.columnconfigure(i, weight=10) 
        #python command
        self.tag_command = tkinter.Label(ctWin, text=self.tr["Python command"])
        self.tag_command.grid(column=0, row=0,sticky="W",pady = 2)
        self.box_command= tkinter.Entry(ctWin)
        self.box_command.grid(column=1, row=0,sticky='ew') 
        self.tag_command_caption = tkinter.Label(ctWin, text=self.tr["Command warning"])
        self.tag_command_caption.grid(column=0, row=1,sticky="W",pady = 5)    

        options = self.load_config_file()
        self.replace_value(self.box_command,options["command"])
        #save options
        self.btn_save_options = tkinter.Button(ctWin,text=self.tr["Save"],command=lambda: self.save_config_file())
        self.btn_save_options.grid(column=1, row=4,sticky="WE") 
           
        ctWin.transient(parent)
        ctWin.grab_set()
        parent.wait_window(ctWin)


    def load_config_file(self):
        config_file = open('gui_assets/config.json')
        return(json.load(config_file))

    def save_config_file(self):
        data = {}
        #get data for our file
        data["command"]=self.box_command.get()
        with open('gui_assets/config.json', 'w') as file:
         file.write(json.dumps(data))
         file.close() 

    def delete_window(self,parent):
      #check a path exist so we can split
      file = self.current_file
      if self.current_file !='':
        file = self.current_file.split("/")[-1]

      message = self.tr["Close message"] % (
            file or "this file")
      save = messagebox.askyesnocancel(
          message=message,
          title="Pms2bemani",
          default=messagebox.YES,
      )
      if save:
          # Cerrar la ventana.
          if self.current_file !='':
            self.save()
            parent.destroy()
            return
          else:
            self.save_as(parent)
          #check we make the safe,
          #if not will repeat ask
          if self.current_file !='':
            parent.destroy()
          if self.current_file =='':
            self.delete_window(parent)
      elif save == False:
          parent.destroy()

    def chara_selection(self,parent,widget,pos):
        # Toplevel object which will
        # be treated as a new window
        ctWin = Toplevel(parent)
        # sets the title of the
        # Toplevel widget
        ctWin.title("Chara selector")  
        ctWin.geometry("200x200")
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)        
        self.grid_rowconfigure(2, weight=0)  
        self.grid_rowconfigure(3, weight=0)  

        #creating text box 
        e = Entry(ctWin)
        e.pack(side='top', fill='x', expand=True)
        e.bind('<KeyRelease>', self.checkkey)

        #buttons
        btn_romaji = Button(ctWin,text="romaji",command=lambda: self.list_to_romaji())
        btn_romaji.pack()
        btn_katakana = Button(ctWin,text="katakana",command=lambda: self.list_to_katakana())
        btn_katakana.pack()
          
        #creating list box
        self.lb = Listbox(ctWin)
        self.lb.pack(side='top', fill='x', expand=True)
        self.lb.bind('<<ListboxSelect>>', lambda eff: self.onselect(eff,widget,pos))
        self.update(self.l)
        
           
        ctWin.transient(parent)
        ctWin.grab_set()
        parent.wait_window(ctWin)
    
    def list_to_romaji(self):
        new_list = []
        katsu = cutlet.Cutlet()
        for line in self.l:
            new_list.append([line[0],katsu.romaji(line[1]),line[2]])
        self.l = new_list 
        self.update(self.l)

    def list_to_katakana(self):
        self.l=self.chara_txt_to_data()
        self.update(self.l)
    
    # Function for checking the
    # key pressed and updating
    # the listbox
    def checkkey(self,event):
           
        value = event.widget.get()
          
        # get data from l
        if value == '':
            data = self.l
        else:
            data = []
            for item in self.l:
                if value.lower() in ''.join(str(x) for x in item).lower():
                    data.append(item)                
       
        # update data in listbox
        self.update(data)
       
       
    def update(self,data):
        # clear previous data
        self.lb.delete(0, 'end')
       
        # put new data
        for item in data:
            self.lb.insert('end', item)

    def onselect(self,event,widget,pos):
        # Note here that Tkinter passes an event object to onselect()
        w = event.widget
        index = int(w.curselection()[0])
        value = w.get(index)
        self.replace_value(widget,value[pos])
        # Hariai in game
        if pos == 2:
            self.hariai_in_game.set(True)

    def chara_txt_to_data(self):
        # Using readlines()
        file = open('gui_assets/chara_list.txt', 'r',encoding="utf8")
        Lines = file.readlines()
        charas = []
        # Strips the newline character
        for line in Lines:
            chara_anim = line.split(',')[0].replace("'",'').strip()
            ha = line.split(',')[15].replace("'",'').strip()
            chara_name = line.split(',')[10].replace("'",'').strip()
            charas.append([chara_anim,chara_name,ha])
        return charas

    

if __name__ == "__main__":

 #start our app
 window = tkinter.Tk()
 app = Application(window)
 window.mainloop()