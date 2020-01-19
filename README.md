# lensranker
Python script for ranking images of strong lensing candidates

## Running the program
Navigate to directory containing the script.
In your terminal of choice, execute the following:
```sh
$ python3 lensranker.py
```
By default, the program looks in your current working directory for images and the save file. If you want to store your images elsewhere, execute one of the following, replacing YOUR/PATH/HERE with your desired path:
```sh
$ python3 lensranker.py -p YOUR/PATH/HERE
```
```sh
$ python3 lensranker.py --path YOUR/PATH/HERE
```
Similarly, if you desire your save file to have a non-default name (default is lensrankings.txt), execute one of the following, replacing FILENAME with your desired filename:
```sh
$ python3 lensranker.py -f FILENAME
```
```sh
$ python3 lensranker.py --filename FILENAME
```
Finally, the default file extension which the script looks for are .jpg images. If you want to run the script on other file types, execute the following, replacing EXTENSION with your desired file extension (without the preceding period -- so if you want to look for .png files, replace it with png): 
```sh
$ python3 lensranker.py --imtype EXTENSION
```

