# region Comment

# This is a simple script to generate the final single file magickcow.py blender addon.
# It simply joins together all of the files that have been separated into segments of their own.
# The reason this is done like this is because a large enough multi-file python program can actually take multiple seconds to start up, and for mcow
# that has proven to actually have a visible performance impact...
# This is commonly known as the "python import time problem"... This comment is here for those who want to criticise my code, so that they know why is it that I did things the way that I did.
# You are free to ignore this, fork my project and make your own thing where you actually use imports if it ever bothers you that much to package all of the code into a final single file addon.

# endregion

def mcow_file_append(write_file, filename):
    with open(filename, "r") as read_file:
        contents = read_file.read()
        write_file.write(contents)
        write_file.write("\n") # I would write \r\n in Windows, but doing so leads to \r\r\n since \n is translated to \r\n automatically when working with "r" and "w" modes rather than "rb" and "wb". In short, python handles text mode operations for us already so we don't have anything to worry about.

def mcow_file_generate(out_filename, in_filenames):
    with open(out_filename, "w") as file:
        try:
            for filename in in_filenames:
                mcow_file_append(file, filename)
        except Exception as e:
            print(f"There was an error generating the output file: {e}")

def main():
    ofilename = "../magickcow.py"
    ifilenames = [
        "../mcow/License.py",
        "../mcow/Comments.py",
        "../mcow/BlenderInfo.py",
        "../mcow/Imports.py",

        "../mcow/Main.py",
    ]
    mcow_file_generate(ofilename, ifilenames)

if __name__ == "__main__":
    main()
