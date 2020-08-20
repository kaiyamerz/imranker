# -*- coding: utf-8 -*-
try:
    import tkinter as tk
    import tkinter.messagebox as messagebox
except:
    import Tkinter as tk
    import tkMessageBox as messagebox
from PIL import ImageTk, Image, ImageShow, ImageFilter, ImageEnhance
ImageShow.Viewer = "PNG"
import numpy as np
import pandas as pd
from io import StringIO
import glob
import argparse
import os
import sys


class MainWindow(object):
    def __init__(self, main, path = '', imtype = 'jpg',
            outfile = 'lensrankings.txt'):
        '''
        Constructor

        Required Inputs:
            main (Tk): root to which the tkinter widgets are added

        Optional Inputs:
            path (string): path to directory containing candidate images
            imtype (string): file extension of images to be ranked
            outfile (string): filename of text file for saving data
        '''
        os.system('xset r off')
        if path == '':
            self.path = os.getcwd()

        else:
            self.path = path

        if self.path[-1] != '/':
            self.path = self.path + '/'

        self.imtype = imtype
        self.outfile = outfile

        #sets up main tk.Tk() object
        self.main = main

        self.main.title("Strong Lensing Ranker")
        self.main.configure(background = 'grey')

        #sets useful attributes
        self.color = tk.BooleanVar(value = False)
        self.edge = tk.BooleanVar(value = False)
        self.fullw = self.main.winfo_screenwidth()
        self.fullh = self.main.winfo_screenheight()
        self.zoomfrac = (self.fullh - 275) / 400
        self._resamp = tk.BooleanVar()
        self._go_back_one = False
        self._df = self._get_images()
        try:
            self.current_index = pd.isnull(self._df).any(1).to_numpy().nonzero()[0][0]
        except IndexError:
            sys.exit("All images have been ranked. If you want to continue ranking,"
                    " please enable resampling and try again.")
        self.initialized = False
        self.current_im = self._next_image()
        self.current_file = self._df.index[self.current_index]
        self.img = None
        
        #sets up the menubar for switching config options manually
        self._settings = tk.Menu(self.main, tearoff = 0)
        self._settings.add_command(label = "Setting_1")
        self._settings.add_command(label = "Setting_2")
        self._settings.add_separator()
        def apply_filter():
            #
            self._redraw()
        self._settings.add_checkbutton(label = "Enhance", variable = self.color, \
                onvalue = True, offvalue = False, command = apply_filter)
        def color_filt(event):
            #
            self.color.set(not self.color.get())
            apply_filter()
        self._settings.add_checkbutton(label = "Contour", variable = self.edge, \
                onvalue = True, offvalue = False, command = apply_filter)
        def edge_filt(event):
            #
            self.edge.set(not self.edge.get())
            apply_filter()
            
        self.main.bind('<Control-f>', color_filt)
        self.main.bind('<Alt-f>', edge_filt)
        self._menubar = tk.Menu(self.main, tearoff = 0)
        self._menubar.add_cascade(label = "Settings", menu = self._settings)
        
        self.main.config(menu = self._menubar)
        
        #sets up canvas object for displaying images and displays the first image
        self._canvas = tk.Canvas(self.main)
        self._canvas.configure(background = 'grey')
        self._canvas.bind("<Configure>", self._resize)
        self._image_on_canvas = self._canvas.create_image(self.fullw // 2, \
                0, anchor = 'n', image = self.current_im)
        self._canvas.pack(fill = 'both', anchor = 'center', side = 'top', \
                expand = True)

        #sets up frame object for organizing buttons and other UI widgets
        self._frame = tk.Frame(self.main)
        self._frame.pack(side='bottom')

        #sets up entry object for scoring
        self._txt = tk.Entry(self._frame, font = ("Arial", 40), \
                width = int(round(6 * self.zoomfrac)))
        self._txt.grid(column = 0, columnspan = 2, row = 2, sticky = 'W')
        self._txt.focus()

        #binds the enter/return key to the score submitting function
        self.main.bind('<Return>', lambda event : self._submit())

        #sets up submit button
        self.button1 = tk.Button(self._frame, text = "submit", font = \
                ("Arial", 30), command = self._submit)
        self.button1.grid(column = 2, columnspan = 2, row = 2, sticky = 'NSEW')

        #binds left arrow key to the going back one image
        self.main.bind('<Left>', lambda event : self._gobackone())

        #sets up the go back one button
        self.button2 = tk.Button(self._frame, text = u"←", font = ("Arial bold", 30), \
                command = self._gobackone)
        self.button2.grid(column = 0, row = 4, sticky = 'W')

        #binds right arrow key to the going back one image
        self.main.bind('<Right>', lambda event : self._skiptofront())

        #sets up the skip forward button
        self.button2 = tk.Button(self._frame, text = u"↠", font = ("Arial", 30), \
                command = self._skiptofront)
        self.button2.grid(column = 3, row = 4, sticky = 'E')

        #sets up another frame object for holding other options (things like
        #   checkboxes and dropdowns which control backend functionality)
        self.optionframe = tk.Frame(self._frame)
        self.optionframe.grid(column = 1, columnspan = 2, row = 4, \
                sticky='W')

        #sets up checkbutton for optional resampling
        self.resample_check = tk.Checkbutton(self.optionframe, \
                text = 'resample', var = self._resamp, onvalue = True, \
                offvalue = False, font = ('Arial', 15))
        self.resample_check.pack(side = 'left', anchor = 'center')

        #sets up text display for showing current position in the images, the
        #   number ranked already, and the name of the current image
        self.current_position = tk.Label(self.optionframe, text = \
        self.current_file + ", current position: " + \
                str(self.current_index + 1) + " out of " + \
                str(len(self._df.index)), font = ("Arial", 15))
        self.current_position.pack(side = 'left', anchor = 'center', padx = 20)

        #overwrites the usual exiting protocol with a user prompt to ensure no
        #   accidental exits occur
        self.main.protocol("WM_DELETE_WINDOW", self._callback)


    def _find_images(self):
        '''
        Finds and returns a list of images of self.imtype located at
            self.path.

        Returns:
            ims (list of strings): filenames
        '''
        ims = glob.glob(self.path + '*.' + self.imtype)

        return ims


    def _get_images(self):
        '''
        Reads the save file at self.path/self.outfile; if no file at that
            path exists, creates one and populates it with the images present
            at self.path.

        Returns:
            df (pandas DataFrame object): pandas DataFrame containing file
                names and scores
        '''
        if not os.path.exists(self.outfile):
            save = open(self.outfile, 'w')
            images = self._find_images()
            df = pd.DataFrame(index = images)
            df['Rank'] = [np.nan] * len(images)
            save.write(df.to_csv(na_rep = '').replace(',', \
                ' ').replace(self.path, '')[6:])
            save.close()

        save = open(self.outfile)
        images = (',Rank\n' + save.read().replace(' ', ','))
        try:
            df = pd.read_csv(StringIO(images), index_col = 0, dtype = str)
        except:
            df = pd.read_csv(StringIO(unicode(images)), index_col = 0, dtype = str)

        return df


    def _make_image(self, impath, rotate = False):
        '''
        Creates and returns a tkinter-compatible image object from image at
            impath, if rotate is True, image is rotated 0, 90, 180, or 270
            degrees before being returned.

        Inputs:
            impath (string): path to the image file
            rotate (boolean): determines if image will be rotated

        Returns:
            img: tkinter-compatible image object
        '''
        img = Image.open(impath)
        if self.initialized:
            img = img.resize(self._maximize(img), Image.ANTIALIAS)
        
        if rotate:
            if not self.current_rot:
                self.current_rot = np.random.randint(low = 0, high = 3)
                
            img = img.rotate(90 * self.current_rot, expand = True)
        
        img = self._apply_filters(img)
        
        self.img = ImageTk.PhotoImage(img)
        img.close()

        return self.img


    def _next_image(self):
        '''
        Determines index for and returns a tkinter-compatible image object
            for the next image, resampling already-ranked images if resampling is
            enabled by the user.

        Returns:
            img: tkinter-compatible image object
        '''
        if pd.isnull(self._df).any(1).to_numpy().nonzero()[0].size > 0:
            randfrac = 0.9
        else:
            randfrac = 0.0
            
        randdec = np.random.rand()
        if self._go_back_one:
            self.current_file = self._df.index[self.current_index]
            self.current_position.configure(text = self.current_file + \
                    ", current position: " + str(self.current_index + 1) + \
                    " out of " + str(len(self._df.index)))
            return (self._make_image(self.path + \
                    self._df.index[self.current_index]))

        elif randdec >= randfrac and self._resamp.get() and self.current_index > 0:
            randnum = np.random.randint(low = 0, high = self.current_index)
            self.current_index = randnum
            self.current_file = self._df.index[self.current_index]
            self.current_position.configure(text = self.current_file + \
                    ", current position: " + str(self.current_index + 1) + \
                    " out of " + str(len(self._df.index)))
            return (self._make_image(self.path + '/'+ \
                    self._df.index[self.current_index], rotate = True))

        elif pd.notna(self._df.iloc[self.current_index].item()):
            next_index = pd.isnull(self._df).any(1).to_numpy().nonzero()[0][0]
            self.current_index = next_index
            self.current_file = self._df.index[self.current_index]
            self.current_position.configure(text = self.current_file + \
                    ", current position: " + str(self.current_index + 1) + \
                    " out of " + str(len(self._df.index)))
            return self._next_image()

        else:
            return (self._make_image(self.path + \
                    self._df.index[self.current_index]))


    def _submit(self):
        '''
        Saves score for current image
        '''
        if self._txt.get() in ['', '0','1','2','3','4']:
            text = self._txt.get()
            if text == '':
                text = '0'

            if self._go_back_one:
                self._df.iloc[self.current_index] = \
                        self._df.iloc[self.current_index].item()[0:-1] + text
                self._go_back_one = False

            elif pd.isna(self._df.iloc[self.current_index].item()):
                self._df.iloc[self.current_index] = text

            else:
                self._df.iloc[self.current_index] = \
                        str(self._df.iloc[self.current_index].item()) + \
                        '.' + text

            self._txt.delete(0, "end")
            self.save_file()
            self._go_back_one = False
            self.current_im = self._next_image()
            self._canvas.itemconfig(self._image_on_canvas, image = self.current_im)

        else:
            self._txt.delete(0, "end")
            messagebox.showwarning("Error", \
                    "Invalid answer, please try again.")
                    
    
    def _maximize(self, img):
        '''
        
        '''
        width = self._canvas.winfo_width()
        height = self._canvas.winfo_height()
        width_ratio = width / img.width
        height_ratio = height / img.height
        max_ratio = (width_ratio, height_ratio)
        
        aspect_ratio = height/width
        
        if max_ratio[1] > max_ratio[0]:
            max_width = width
            max_height = int(img.height * max_ratio[0])
            
        elif max_ratio[0] > max_ratio[1]:
            max_width = int(img.width * max_ratio[1])
            max_height = height
            
        else:
            max_width = width
            max_height = height
            
        return(max_width, max_height)
        
        
    def _resize(self, event):
        '''
        
        '''
        if self.initialized:
            delta_x = self.fullw - event.width
            self.fullw = event.width
            img = self._make_image(self.path + self._df.index[self.current_index])
            self.current_im = img
            self._canvas.itemconfig(self._image_on_canvas, image = self.current_im)
            self._canvas.move(self._image_on_canvas, -delta_x//2, 0)
        self.initialized = True
        
        
    def _redraw(self):
        '''
        
        '''
        img = self._make_image(self.path + self._df.index[self.current_index])
        self.current_im = img
        self._canvas.itemconfig(self._image_on_canvas, image = self.current_im)
        
        
    def _apply_filters(self, img):
        '''
        
        '''
        if self.color.get():
            filt = ImageFilter.UnsharpMask(radius = 25, percent = 200, threshold = 30)
            img = img.filter(filt)
            
        if self.edge.get():
            #img = img.convert("LA")
            #filt = ImageFilter.SHARPEN()
            #img = img.filter(filt)
            #enh = ImageEnhance.Brightness(img)
            #img = enh.enhance(0.25)
            enh = ImageEnhance.Contrast(img)
            image = enh.enhance(1.5)
            #enh = ImageEnhance.Brightness(img)
            #img = enh.enhance(0.75)
            filt = ImageFilter.UnsharpMask(radius = 50, percent = 150, threshold = 30)
            img = img.filter(filt)
            filt = ImageFilter.EDGE_ENHANCE_MORE()
            img = img.filter(filt)
            filt = ImageFilter.CONTOUR()
            img = img.filter(filt)
            
        return img


    def _gobackone(self):
        '''
        Changes current image to the previous (non-resampled) image
        in self._df.
        '''
        if self.current_index != 0:
            self._go_back_one = True
            self.current_index -= 1
            self.current_im = self._next_image()
            self._canvas.itemconfig(self._image_on_canvas, \
                    image = self.current_im)


    def _skiptofront(self):
        '''
        Changes current image to the next (non-resampled) image in self._df
        '''
        self._go_back_one = False
        self.current_im = self._next_image()
        self._canvas.itemconfig(self._image_on_canvas, \
                image = self.current_im)


    def _callback(self):
        '''
        Overwrites the (x) button's default functionality so that it asks the
        user before closing the application
        '''
        if messagebox.askokcancel("Quit", \
                "Do you really wish to quit?"):
            self.save_file()
            os.system('xset r on')
            self.main.destroy()


    def save_file(self):
        '''
        Saves current dataframe into path/outfile.txt
        '''
        save = open(self.outfile, 'w')
        save.write(self._df.to_csv().replace(',', ' ')[6:])
        save.close()


    def execute(self):
        '''
        Displays main window to user, activates bindings
        '''
        try:
            self.main.mainloop()
        except KeyboardInterrupt:
            self.save_file()
            os.system('xset r on')
            self.main.destroy()


if __name__ == '__main__':
    ### Read Arguments
    # Set up argument parser - Generic parameters
    parser = argparse.ArgumentParser(description="Lens Ranker")
    parser.add_argument('-p', '--path', default = '', type = str,
            help = 'path to directory containing data to be ranked (also looks \
            for the save file there)')
    parser.add_argument('-f', '--filename', default = 'imagerankings.txt', \
            type = str, help = 'file name for the .txt file (if no file of this \
            name exists, one will be created)')
    parser.add_argument('--imtype', default = 'jpg', type = str, \
            help = 'image type to be loaded in')

    args = parser.parse_args()
    arglist=vars(args)

    if arglist['path'] == '':
        path = os.getcwd()
    else:
        path = arglist['path']

    if path[-1] != '/':
        path = path + '/'

    imtype = arglist['imtype']

    outfile = arglist['filename']

    MainWindow(tk.Tk(), path = path, imtype = imtype, \
            outfile = outfile).execute()
