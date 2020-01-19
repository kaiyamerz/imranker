import tkinter as tk
import tkinter.messagebox
from PIL import ImageTk, Image
import numpy as np
import pandas as pd
import glob
import argparse
import os
    
    
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
        if path == '':
            self.path = os.getcwd() + '/'
            
        else:
            self.path = path + '/'
        
        self.imtype = imtype
        self.outfile = outfile

        #sets up main tk.Tk() object
        self.main = main
        self.main.attributes('-zoomed', True)
        self.main.title("Strong Lensing Ranker")
        self.main.configure(background = 'grey')
        
        #sets useful attributes
        self.fullw = self.main.winfo_screenwidth()
        self.fullh = self.main.winfo_screenheight()
        self.zoomfac = (self.fullh - 275) / 456
    
        self._resamp = tk.BooleanVar()
        
        self._df = self._get_images()
        self.current_index = 0
    
        self.current_im = self._next_image()
        print(self.current_index)
        
        self._canvas = tk.Canvas(self.main)
        self._canvas.configure(background = 'grey')
        self._image_on_canvas = self._canvas.create_image(self.fullw // 2, \
                self.fullh//2 - 130, anchor = 'center', image = self.current_im)
        self._canvas.pack(fill = 'both', anchor = 'center', side = 'top', \
            expand = True)
    
        self._frame = tk.Frame(self.main)
        self._frame.pack(side='bottom')
            
        self._txt = tk.Entry(self._frame, font = ("Arial", 40), \
                width = round(7 * self.zoomfac))
        self._txt.grid(column = 0,row = 2, sticky = 'W')
        self._txt.focus()
            
            
        def _submit():
            '''
            Saves score for current image
            '''
            print('SUBMITTING SCORES')
            if self._txt.get() in ['', '0','1','2','3']:
                text = self._txt.get()
                if text == '':
                    text = '0'
                       
                if pd.isna(self._df.iloc[self.current_index].item()):
                    self._df.iloc[self.current_index] = text
                else:
                    self._df.iloc[self.current_index] = \
                            str(self._df.iloc[self.current_index].item()) + '.' + text
                self._txt.delete(0, "end")
                self.save_file()

                self.current_im = self._next_image()
                self._canvas.itemconfig(self._image_on_canvas, \
                    image = self.current_im)
            else:
                self._txt.delete(0, "end")
                tkinter.messagebox.showwarning("Error", \
                        "Invalid answer, please try again.")
            text = ''
            
        self.main.bind('<Return>', lambda event : _submit())
            
        self.button1 = tk.Button(self._frame, text = "submit", font = \
                ("Arial", 30), command = _submit)
        self.button1.grid(column = 1, columnspan = 2, row = 2, sticky = 'NSEW')
            
        def gobackone():
            '''
            Changes current image to the previous (non-resampled) image in self._df
            '''
            self.current_index -= 1
            self.current_im = self._make_image(self.path + self._df.index[self.current_index])
            self._canvas.itemconfig(self._image_on_canvas, image = self.current_im)
            
        self.main.bind('<Left>', lambda event : gobackone())
            
        self.button2 = tk.Button(self._frame, text = "←", font = ("Arial", 30), \
                command = gobackone)
        self.button2.grid(column = 0, row = 4, sticky = 'W')
        
        def goforwardone():
            '''
            Changes current image to the next (non-resampled) image in self._df
            '''
            self.current_index += 1
            self.current_im = self._make_image(self.path + self._df.index[self.current_index])
            self._canvas.itemconfig(self._image_on_canvas, image = self.current_im)
    
        self.main.bind('<Right>', lambda event : goforwardone())
        
        self.button3 = tk.Button(self._frame, text = "→", font = ("Arial", 30), \
                command = goforwardone)
        self.button3.grid(column = 2, row = 4, sticky = 'E')
        
        self.optionframe = tk.Frame(self._frame)
        self.optionframe.grid(column = 1, row = 4, sticky='NSEW')
        
        self.resample_check = tk.Checkbutton(self.optionframe, \
                text = 'resample', var = self._resamp, onvalue = True, \
                offvalue = False, font = ('Arial', 15))
        self.resample_check.pack(side = 'left', anchor = 'w', padx = 20)
            
        def _callback():
            '''
            Overwrites the (x) button's default functionality so that it asks the
            user before closing the application
            '''
            if tkinter.messagebox.askokcancel("Quit", "Do you really wish to quit?"):
                self.save_file()
                self.main.destroy()
            
        self.main.protocol("WM_DELETE_WINDOW", _callback)
        
        
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
        df = pd.read_csv(pd.compat.StringIO(images), index_col = 0, dtype = str)
        
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
        img = img.resize((round(img.width * self.zoomfac), \
                round(img.height * self.zoomfac)), Image.ANTIALIAS)
                
        if rotate:
            rot_times = np.random.randint(low = 0, high = 3)
            img = img.rotate(90 * rot_times, expand = True)
        img = ImageTk.PhotoImage(img)
        
        return img
        
        
    def _next_image(self):
        '''
        Determines index for and returns a tkinter-compatible image object
            the next image, resampling already-ranked images if resampling is
            enabled by the user.

        Returns:
            img: tkinter-compatible image object
        '''
        randdec = np.random.rand()
        
        if randdec >= 0.9 and self._resamp.get() and self.current_index > 0:
            randnum = np.random.randint(low = 0, high = self.current_index)
            self.current_index = randnum
            return (self._make_image(self.path + '/'+ \
                    self._df.index[self.current_index], rotate = True))
                    
        elif pd.notna(self._df.iloc[self.current_index].item()):
            self.current_index += 1
            return self._next_image()
            
        else:      
            return (self._make_image(self.path + \
                    self._df.index[self.current_index]))
        
        
    def save_file(self):
        '''
        Saves current dataframe into path/outfile.txt
        '''
        save = open(self.outfile, 'w')
        save.write(self._df.to_csv().replace(',', ' ')[6:])
        save.close()


    def execute(self):
        '''
        Sets certain parameters based on user provided arguments when
            lensranker.py is run from the terminal
        '''
        ### Read Arguments
        # Set up argument parser - Generic parameters
        parser = argparse.ArgumentParser(description="Lens Ranker")
        parser.add_argument('-p', '--path', default = '', type = str,
                            help = 'path to directory containing data to be ranked\
                            (also creates the .txt file there')
        parser.add_argument('imtype', default = 'jpg', type = str, nargs='?',
                            help = 'input files pathname',)
        parser.add_argument('outfile', default = 'lensrankings.txt', type = str, nargs='?',
                            help = 'file name for the .txt file (if no file of this name exists, one will\
                            be created')

        args = parser.parse_args()
        self.arglist=vars(args)
        print(self.arglist)
        if self.arglist['path'] == '':
            self.path = os.getcwd() + '/'
        else:
            self.path = self.arglist['path'] + '/'
            
        self.imtype = self.arglist['imtype']
        
        self.outfile = self.arglist['outfile']
        
        self.main.mainloop()
                
        
if __name__ == '__main__':
    MainWindow(tk.Tk()).execute()
